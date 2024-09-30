import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, File, HTTPException, Path, Query, UploadFile
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text

from src.config import get_app_settings
from src.database import get_db
from src.models.src import SKU
from src.parsers.xml_parser import XMLParser
from src.schemas import FileResponse, JobResponse, ProgressResponse, SimilarSKUResponse, SKUResponse, UploadResponse
from src.services.elasticsearch_service import ElasticsearchService
from src.services.sku_service import SKUService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_app_settings()
DATA_DIR = "./data"

es_client = AsyncElasticsearch(
    hosts=[
        {
            "host": settings.ELASTIC_HOST,
            "port": settings.ELASTIC_PORT,
            "scheme": "http",
        }
    ],
    basic_auth=("elastic", settings.ELASTIC_PASSWORD),
)
es_service = ElasticsearchService(es_client)
xml_parser = XMLParser()

job_progress: dict[str, dict[str, float]] = {}
job_progress_lock = asyncio.Lock()


@asynccontextmanager
async def app_lifespan(app_: FastAPI) -> AsyncIterator[None]:
    yield
    await es_service.close()


app = FastAPI(lifespan=app_lifespan)

app.mount("/data", StaticFiles(directory="data"), name="data")


@app.get(
    "/files",
    summary="List available XML files",
    description="Fetches a list of available XML files in the mounted `data` directory.",
)
async def list_files() -> FileResponse:
    """
    Lists all XML files that are available for processing in the `data` directory.

    Returns:
    - A list of filenames (XML files) found in the directory.

    Raises:
    - 500 Internal Server Error if there was an issue accessing the files.
    """
    try:
        files = os.listdir(DATA_DIR)
        xml_files = [f for f in files if f.endswith(".xml")]
        return FileResponse(files=xml_files)
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/upload",
    summary="Upload a new XML file",
    description="Uploads a new XML file to the `data` directory.",
)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """
    Uploads a new XML file to the server and saves it to the `data` directory.

    Args:
    - `file`: The XML file being uploaded (multipart/form-data).

    Returns:
    - The filename of the uploaded file.

    Raises:
    - 500 Internal Server Error if the file upload fails.
    """
    try:
        if file.filename is None:
            raise ValueError("No filename provided in the uploaded file.")

        file_location = os.path.join(DATA_DIR, file.filename)

        content = await file.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return UploadResponse(filename=file.filename)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/process",
    summary="Start processing an XML file",
    description=(
        "Starts the processing of the specified XML file. "
        "Returns a unique job ID that can be used to track progress."
    ),
)
async def process_file(filename: str = Query(..., description="The name of the XML file to process")) -> JobResponse:
    """
    Starts processing the specified XML file.

    Args:
    - `filename`: The name of the XML file to process (must be available in the `data` directory).

    Returns:
    - A message indicating the job has started.
    - The UUID of the job that can be used to track its progress.

    Raises:
    - 404 Not Found if the specified file does not exist.
    - 500 Internal Server Error if the processing could not be started.
    """
    try:
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        job_id = str(uuid.uuid4())
        async with job_progress_lock:
            job_progress[job_id] = {
                "processing_progress": 0.0,
                "update_similar_progress": 0.0,
            }
        asyncio.create_task(process_xml_file(file_path, job_id))

        return JobResponse(message="Processing started", job_id=job_id)
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/progress/{job_id}",
    summary="Get the progress of a processing job",
    description="Returns the current progress (in percentage) of a job given its UUID.",
)
async def get_progress(
    job_id: str = Path(..., description="The UUID of the job to query progress for")
) -> ProgressResponse:
    """
    Fetches the progress of a job by its UUID.

    Args:
    - `job_id`: The UUID of the processing job.

    Returns:
    - The job ID and its current progress as a percentage.

    Raises:
    - 404 Not Found if the job ID does not exist.
    """
    async with job_progress_lock:
        progress_data = job_progress.get(job_id)
    if progress_data is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return ProgressResponse(
        job_id=job_id,
        processing_progress=progress_data.get("processing_progress", 0.0),
        update_similar_progress=progress_data.get("update_similar_progress", 0.0),
    )


@app.get(
    "/sku/{uuid}",
    summary="Get SKU by UUID",
    description="Returns the SKU information including similar SKUs.",
)
async def get_sku(uuid: str = Path(..., description="The UUID of the SKU")) -> SKUResponse:
    """
    Retrieves SKU details by UUID, including similar SKUs.

    Args:
    - `uuid`: The UUID of the SKU.

    Returns:
    - The SKU details, including similar SKUs.

    Raises:
    - 404 Not Found if the SKU does not exist.
    """
    async for session in get_db():
        async with session.begin():
            sku_service = SKUService(session)
            sku = await sku_service.get_sku_by_uuid(uuid)
            if not sku:
                raise HTTPException(status_code=404, detail="SKU not found")

            similar_skus: list[SKU] = []
            if sku.similar_sku:
                result = await session.execute(select(SKU).where(SKU.uuid.in_(sku.similar_sku)))
                similar_skus = list(result.scalars().all())

            sku_response = SKUResponse(
                uuid=str(sku.uuid),
                product_id=sku.product_id,
                title=sku.title,
                category_lvl_1=sku.category_lvl_1,
                category_lvl_2=sku.category_lvl_2,
                category_lvl_3=sku.category_lvl_3,
                category_remaining=sku.category_remaining,
                similar_sku=[
                    SimilarSKUResponse(
                        uuid=str(s.uuid),
                        title=s.title,
                    )
                    for s in similar_skus
                ],
            )
            return sku_response
    raise HTTPException(status_code=500, detail="Internal Server Error")


async def process_xml_file(xml_file: str, job_id: str) -> None:
    try:
        total_offers = xml_parser.count_offers(xml_file)
        processed_offers = 0

        categories = xml_parser.parse_categories(xml_file)

        await clear_elasticsearch_index()
        await clear_sku_table()

        await es_service.create_index(
            "products",
            index_body={
                "mappings": {
                    "properties": {
                        "name": {"type": "text", "analyzer": "russian"},
                        "description": {"type": "text", "analyzer": "russian"},
                    }
                }
            },
        )

        async for session in get_db():
            async with session.begin():
                sku_service = SKUService(session)
                for offer_data in xml_parser.parse_offers(xml_file):
                    offer_id = offer_data["offer_id"]
                    sku_uuid = str(uuid.uuid4())

                    hierarchy = xml_parser.get_category_hierarchy(categories, offer_data["category_id"])
                    category_lvl_1 = hierarchy[0] if len(hierarchy) > 0 else None
                    category_lvl_2 = hierarchy[1] if len(hierarchy) > 1 else None
                    category_lvl_3 = hierarchy[2] if len(hierarchy) > 2 else None
                    category_remaining = "/".join(hierarchy[3:]) if len(hierarchy) > 3 else None

                    sku_data: dict[str, Any] = {
                        "uuid": sku_uuid,
                        "marketplace_id": 1,
                        "offer_id": offer_id,
                        "name": offer_data["name"],
                        "description": offer_data["description"],
                        "vendor": offer_data["vendor"],
                        "barcode": offer_data["barcode"],
                        "category_id": offer_data["category_id"],
                        "category_lvl_1": category_lvl_1,
                        "category_lvl_2": category_lvl_2,
                        "category_lvl_3": category_lvl_3,
                        "category_remaining": category_remaining,
                        "params": offer_data["params"],
                        "price": offer_data["price"],
                        "picture": offer_data["picture"],
                        "currency_id": offer_data["currency_id"],
                    }

                    await sku_service.save_sku(sku_data)

                    doc = {
                        "uuid": sku_uuid,
                        "name": offer_data["name"],
                        "description": offer_data["description"],
                        "vendor": offer_data["vendor"],
                        "barcode": offer_data["barcode"],
                        "category_id": offer_data["category_id"],
                        "price": offer_data["price"],
                        "params": offer_data["params"],
                    }

                    await es_service.index_document(index_name="products", doc_id=sku_uuid, document=doc)

                    processed_offers += 1
                    progress = (processed_offers / total_offers) * 100.0
                    async with job_progress_lock:
                        job_progress[job_id]["processing_progress"] = progress

                await session.commit()

        await es_service.refresh_index("products")

        async with job_progress_lock:
            job_progress[job_id]["processing_progress"] = 100.0

        await update_similar_skus(job_id)

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing XML file: {e}")
        async with job_progress_lock:
            job_progress[job_id]["processing_progress"] = -1.0

    finally:
        pass


async def clear_elasticsearch_index() -> None:
    index_name = "products"
    if await es_client.indices.exists(index=index_name):
        logger.info(f"Deleting Elasticsearch index '{index_name}'")
        await es_client.indices.delete(index=index_name)
    logger.info(f"Creating Elasticsearch index '{index_name}'")
    index_body = {
        "mappings": {
            "properties": {
                "name": {"type": "text", "analyzer": "russian"},
                "description": {"type": "text", "analyzer": "russian"},
            }
        }
    }
    await es_service.create_index(index_name, index_body)


async def clear_sku_table() -> None:
    async for session in get_db():
        async with session.begin():
            logger.info("Clearing 'sku' table in the database")
            await session.execute(text("TRUNCATE TABLE public.sku RESTART IDENTITY CASCADE"))
            await session.commit()


async def update_similar_skus(job_id: str) -> None:
    async for session in get_db():
        async with session.begin():
            result = await session.execute(select(SKU))
            skus = result.scalars().all()
            total_skus = len(skus)
            processed_skus = 0

            for sku in skus:
                similar_uuids: list[str] = await es_service.search_similar(index_name="products", sku=sku)
                similar_uuids_as_uuid: list[uuid.UUID] = [uuid.UUID(uuid_str) for uuid_str in similar_uuids]
                sku.similar_sku = similar_uuids_as_uuid
                session.add(sku)
                processed_skus += 1
                progress = (processed_skus / total_skus) * 100.0
                async with job_progress_lock:
                    job_progress[job_id]["update_similar_progress"] = progress
            await session.commit()
