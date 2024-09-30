from typing import Any

from elasticsearch import AsyncElasticsearch, RequestError

from src.models.src.modules.sku import SKU


class ElasticsearchService:
    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client

    async def create_index(self, index_name: str, index_body: dict[str, Any]) -> None:
        try:
            await self.es.indices.create(index=index_name, body=index_body)
        except RequestError as e:
            if e.error == "resource_already_exists_exception":
                pass
            else:
                raise

    async def delete_index(self, index_name: str) -> None:
        await self.es.indices.delete(index=index_name)

    async def index_document(self, index_name: str, doc_id: str, document: dict[str, Any]) -> None:
        await self.es.index(index=index_name, id=doc_id, document=document)

    async def search_similar(self, index_name: str, sku: SKU) -> list[str]:
        query = {
            "query": {
                "more_like_this": {
                    "fields": ["name", "description", "vendor"],
                    "like": [
                        {
                            "doc": {
                                "name": sku.title,
                                "description": sku.description,
                                "vendor": sku.brand,
                            }
                        }
                    ],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                }
            }
        }
        response = await self.es.search(index=index_name, body=query, size=5)
        similar_uuids = []
        for hit in response["hits"]["hits"]:
            similar_uuid = hit["_id"]
            if similar_uuid != sku.uuid:
                similar_uuids.append(similar_uuid)
        return similar_uuids

    async def refresh_index(self, index_name: str) -> None:
        await self.es.indices.refresh(index=index_name)

    async def close(self) -> None:
        await self.es.close()
