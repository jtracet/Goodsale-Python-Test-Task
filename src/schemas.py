from pydantic import BaseModel


class FileResponse(BaseModel):
    files: list[str]


class UploadResponse(BaseModel):
    filename: str


class JobResponse(BaseModel):
    message: str
    job_id: str


class ProgressResponse(BaseModel):
    job_id: str
    processing_progress: float
    update_similar_progress: float


class SimilarSKUResponse(BaseModel):
    uuid: str
    title: str | None


class SKUResponse(BaseModel):
    uuid: str
    product_id: int
    title: str | None
    category_lvl_1: str | None
    category_lvl_2: str | None
    category_lvl_3: str | None
    category_remaining: str | None
    similar_sku: list[SimilarSKUResponse] | None
