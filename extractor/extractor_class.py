from pathlib import Path
import pdfplumber
import pandas as pd
import fitz
import cv2
import numpy as np
import pytesseract
import re
from sklearn.cluster import DBSCAN
from PIL import Image
class ScientificPDFExtractor:
    def __init__(self,pdf_path:Path,root:Path):
        self.pdf_path=Path(pdf_path)
        self.root=Path(root)
        self.images_dir=self.root/"images"
        self.outputs_dir=self.root/"outputs"
        self.full_pdf_dir=self.root/"full_pdf"
        self.final_csv_dir=self.root/"final_csv"
        self.images_dir.mkdir(parents=True,exist_ok=True)
        self.outputs_dir.mkdir(parents=True,exist_ok=True)
        self.full_pdf_dir.mkdir(parents=True,exist_ok=True)
        self.final_csv_dir.mkdir(parents=True,exist_ok=True)
        self.results=[]
        self.tables=[]
        self.images=[]
        self.values=[]
        self.graphs=[]
    def add_result(self,data):
        self.results.append(data)
    def save_final_csv(self,name="all_extracted.csv"):
        df=pd.DataFrame(self.results)
        path=self.final_csv_dir/name
        df.to_csv(path,index=False,encoding="utf-8-sig")
        return df
    def render_pages(self,dpi=300):
        doc=fitz.open(self.pdf_path)
        paths=[]
        for i,page in enumerate(doc):
            pix=page.get_pixmap(dpi=dpi)
            path=self.images_dir/f"page_{i+1}.png"
            pix.save(path)
            paths.append(path)
        doc.close()
        return paths
    def mm_to_points(self,mm):
        return float(mm)*72/25.4

    def crop_pdf_region(self, page_num, top_mm, left_mm, width_mm, height_mm, name):
        output = self.images_dir / f"{name}.png"
        bbox = self.convert_bbox_mm(
            top_mm,
            left_mm,
            width_mm,
            height_mm
        )
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[page_num]
            crop = page.crop(bbox)
            img = crop.to_image(resolution=300)
            img.save(output)
        return output, bbox
    def extract_caption(self, page_num, top_mm, height_mm):
        top = self.mm_to_points(top_mm)
        height = self.mm_to_points(height_mm)
        bottom = top + height
        caption = []
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[page_num]
            words = page.extract_words()
        for word in words:
            if bottom <= word["top"] <= bottom + 120:
                caption.append(word["text"])
        return " ".join(caption)
    def image_ocr(self,image_path):
        img=Image.open(image_path)
        return pytesseract.image_to_string(img).replace("\n"," ").strip()
    def cluster_table_columns(self,df,eps=35):
        x=df["x0"].values.reshape(-1,1)
        model=DBSCAN(eps=eps,min_samples=1)
        df["column"]=model.fit_predict(x)
        centers=df.groupby("column")["x0"].mean().sort_values()
        mapping={v:i for i,v in enumerate(centers.index)}
        df["column"]=df["column"].map(mapping)
        return df
    def cluster_table_rows(self,df,eps=5):
        y=df["top"].values.reshape(-1,1)
        model=DBSCAN(eps=eps,min_samples=1)
        df["row"]=model.fit_predict(y)
        centers=df.groupby("row")["top"].mean().sort_values()
        mapping={v:i for i,v in enumerate(centers.index)}
        df["row"]=df["row"].map(mapping)
        return df
    def extract_table_words(self,page_num,bbox):
        with pdfplumber.open(self.pdf_path) as pdf:
            page=pdf.pages[page_num]
            crop=page.crop(bbox)
            words=crop.extract_words(
                keep_blank_chars=False,
                use_text_flow=True
            )
        df=pd.DataFrame(words)
        if len(df)==0:
            return pd.DataFrame()
        df=df[["text","x0","x1","top","bottom"]]
        df=df.sort_values(["top","x0"])
        return df
    def build_table_from_words(self,df):
        df=self.cluster_table_columns(df)
        df=self.cluster_table_rows(df)
        rows=[]
        max_col=int(df["column"].max())
        for row_id in sorted(df["row"].unique()):
            row=[]
            current=df[df["row"]==row_id].sort_values("column")
            for col in range(max_col+1):
                cell=current[current["column"]==col]
                if len(cell):
                    value=" ".join(cell["text"].astype(str))
                else:
                    value=""
                row.append(value)
            rows.append(row)
        return pd.DataFrame(rows)

    def extract_table(self, page_num, top_mm, left_mm, width_mm, height_mm, name):
        image_path, bbox = self.crop_pdf_region(
            page_num,
            top_mm,
            left_mm,
            width_mm,
            height_mm,
            name
        )
        words = self.extract_table_words(
            page_num,
            bbox
        )
        if words.empty:
            return None
        table = self.build_table_from_words(words)
        csv_path = self.outputs_dir / f"{name}.csv"
        table.to_csv(
            csv_path,
            index=False,
            header=False,
            encoding="utf-8-sig"
        )
        self.add_result(
            {
                "type": "table",
                "name": name,
                "page": page_num + 1,
                "image_path": str(image_path),
                "csv_path": str(csv_path)
            }
        )
        return table

    def convert_bbox_mm(self, top_mm, left_mm, width_mm, height_mm):
        top = self.mm_to_points(top_mm)
        left = self.mm_to_points(left_mm)
        width = self.mm_to_points(width_mm)
        height = self.mm_to_points(height_mm)
        return (
            left,
            top,
            left + width,
            top + height
        )
    def extract_page_text(self):
        pages=[]
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num,page in enumerate(pdf.pages):
                text=page.extract_text()
                if text:
                    pages.append({
                        "page":page_num+1,
                        "text":text
                    })
        return pages
    def extract_patterns(self,patterns,context=80):
        pages=self.extract_page_text()
        results=[]
        for page in pages:
            text=page["text"]
            for name,pattern in patterns.items():
                matches=re.finditer(pattern,text,re.IGNORECASE)
                for match in matches:
                    start=max(0,match.start()-context)
                    end=min(len(text),match.end()+context)
                    evidence=text[start:end].replace("\n"," ")
                    groups=match.groups()
                    if len(groups)==1:
                        value=groups[0]
                    elif len(groups)>1:
                        value=" | ".join(groups)
                    else:
                        value=match.group()
                    results.append({
                        "type":"parameter",
                        "parameter":name,
                        "value":value,
                        "page":page["page"],
                        "text_evidence":evidence
                    })
        df=pd.DataFrame(results)
        path=self.outputs_dir/"regex_parameters.csv"
        df.to_csv(
            path,
            index=False,
            encoding="utf-8-sig"
        )
        for row in results:
            self.add_result(row)
        return df

    def extract_graph(self, page_num, top_mm, left_mm, width_mm, height_mm, name, x_min, x_max, y_min, y_max):
        image_path, bbox = self.crop_pdf_region(
            page_num,
            top_mm,
            left_mm,
            width_mm,
            height_mm,
            name
        )
        points = self.extract_graph_points(
            image_path,
            x_min,
            x_max,
            y_min,
            y_max
        )
        csv_path = self.outputs_dir / f"{name}_points.csv"
        points.to_csv(
            csv_path,
            index=False,
            encoding="utf-8-sig"
        )
        self.add_result(
            {
                "type": "graph",
                "name": name,
                "image": str(image_path),
                "points_csv": str(csv_path)
            }
        )
        return points

    def extract_graph_points(self, image_path, x_min, x_max, y_min, y_max):

        img = cv2.imread(str(image_path))
        if img is None:
            return pd.DataFrame()
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        debug_path = image_path.parent / f"{image_path.stem}_processed.png"
        cv2.imwrite(str(debug_path), thresh)
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        points = []
        filtered_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            if area < 3 or area > 150:
                filtered_count += 1
                continue
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity < 0.2:
                    filtered_count += 1
                    continue
            M = cv2.moments(contour)
            if M["m00"] != 0:
                px = M["m10"] / M["m00"]
                py = M["m01"] / M["m00"]

                x = x_min + (px / w) * (x_max - x_min)
                y = y_max - (py / h) * (y_max - y_min)

                points.append({
                    "x": round(x, 4),
                    "y": round(y, 4),
                    "pixel_x": round(px, 2),
                    "pixel_y": round(py, 2)
                })

        if not points:
            return pd.DataFrame()

        points_df = pd.DataFrame(points)

        if len(points_df) > 1:
            try:
                from sklearn.cluster import DBSCAN
                coords = points_df[['x', 'y']].values
                x_range = x_max - x_min
                y_range = y_max - y_min
                eps = min(x_range, y_range) * 0.005 if min(x_range, y_range) > 0 else 0.01

                clusters = DBSCAN(eps=eps, min_samples=1).fit(coords)
                points_df['cluster'] = clusters.labels_

                unique_points = points_df.groupby('cluster').agg({
                    'x': 'mean',
                    'y': 'mean',
                    'pixel_x': 'mean',
                    'pixel_y': 'mean'
                }).reset_index(drop=True)

                return unique_points.round(4)

            except ImportError:
                return points_df

        return points_df