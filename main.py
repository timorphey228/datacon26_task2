from pathlib import Path
from extractor.extractor_class import ScientificPDFExtractor
from papers.article1.config import *

extractor = ScientificPDFExtractor(
    Path(PDF_PATH),
    Path('papers/article1'),
)

for table in TABLES:
    extractor.extract_table(
        page_num = table["page"],
        top_mm = table["top_mm"],
        left_mm = table["left_mm"],
        width_mm = table["width_mm"],
        height_mm = table["height_mm"],
        name = table["name"]
    )

for image in IMAGES:
    extractor.crop_pdf_region(
        page_num=table["page"],
        top_mm=table["top_mm"],
        left_mm=table["left_mm"],
        width_mm=table["width_mm"],
        height_mm=table["height_mm"],
        name=table["name"]
    )
    caption = extractor.extract_caption(
        image["page"],
        image["top_mm"],
        image["height_mm"]
    )
    extractor.add_result(
        {
            "type": "image",
            "name": image["name"],
            "page": image["page"] + 1,
            "path": str(Path),
            "caption": caption
        }
    )
for graph in GRAPHS:
    extractor.extract_graph(
        page_num=graph["page"],
        top_mm=graph["top_mm"],
        left_mm=graph["left_mm"],
        width_mm=graph["width_mm"],
        height_mm=graph["height_mm"],
        name=graph["name"],
        x_min=graph["x_min"],
        x_max=graph["x_max"],
        y_min=graph["y_min"],
        y_max=graph["y_max"]
    )
extractor.extract_patterns(
    PATTERNS
)
final=extractor.save_final_csv(
    "article_all_data.csv"
)
print(final)