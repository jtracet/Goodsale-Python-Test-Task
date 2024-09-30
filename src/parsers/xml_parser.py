from typing import Any, Generator

from lxml import etree


class XMLParser:
    def count_offers(self, xml_file: str) -> int:
        count = 0
        context = etree.iterparse(xml_file, events=("end",), tag="offer")
        for event, elem in context:
            count += 1
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context
        return count

    def parse_categories(self, xml_file: str) -> dict[str, dict[str, str | None]]:
        categories: dict[str, dict[str, str | None]] = {}
        context = etree.iterparse(xml_file, events=("start", "end"))

        for event, elem in context:
            if event == "start" and elem.tag == "categories":
                # Start parsing categories section
                for event_cat, elem_cat in context:
                    if event_cat == "end" and elem_cat.tag == "category":
                        category_id = elem_cat.get("id")
                        parent_id = elem_cat.get("parentId")
                        name = elem_cat.text.strip() if elem_cat.text else ""
                        categories[category_id] = {"name": name, "parent_id": parent_id}
                        elem_cat.clear()
                    elif event_cat == "end" and elem_cat.tag == "categories":
                        break  # Finished parsing categories
            elif event == "end" and elem.tag == "categories":
                break  # Finished parsing categories

        del context
        return categories

    def parse_offers(self, xml_file: str) -> Generator[dict[str, Any], None, None]:
        context = etree.iterparse(xml_file, events=("end",), tag="offer")
        for event, elem in context:
            offer_data = {
                "offer_id": elem.get("id"),
                "name": elem.findtext("name"),
                "description": elem.findtext("description"),
                "vendor": elem.findtext("vendor"),
                "barcode": elem.findtext("barcode"),
                "category_id": elem.findtext("categoryId"),
                "currency_id": elem.findtext("currencyId"),
                "price": elem.findtext("price"),
                "params": {param.get("name"): param.text for param in elem.findall("param")},
                "picture": elem.findtext("picture"),
            }
            yield offer_data
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context

    def get_category_hierarchy(self, categories: dict[str, dict[str, str | None]], category_id: str) -> list[str]:
        hierarchy: list[str] = []
        current_id: str | None = category_id

        while current_id:
            category = categories.get(current_id)
            if category:
                name = category["name"]
                if name is not None:
                    hierarchy.insert(0, name)
                current_id = category["parent_id"]
            else:
                break
        return hierarchy
