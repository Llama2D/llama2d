from dataclasses import dataclass
from typing import List, Tuple

from google.cloud import vision

from ..constants import SECRETS_FILE


@dataclass
class ImageAnnotation:
    text: str  # the word
    midpoint: Tuple[float, float]  # the UNNORMALIZED midpoint of the word, (X,Y)
    midpoint_normalized: Tuple[
        float, float
    ]  # the normalized midpoint between 0 - 1  (X,Y)


@dataclass
class ImageAnnotatorResponse:
    full_text: str  # full text
    orig_text_dims: Tuple[
        float, float
    ]  # the dimension of the *TEXT PORTION* of the image

    words: List[ImageAnnotation]  # a list of words and their midpoints


class ImageAnnotator(object):
    def __init__(self, credentials=SECRETS_FILE):
        try:
            import os

            print(os.getcwd())
            self.client = vision.ImageAnnotatorClient.from_service_account_file(
                credentials
            )
        except Exception as e:
            raise ValueError("OCR Object creation FAILED!\n\n@@@HINT: did you get secrets/google-vision.json from the slack channel?")

        self.__features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]

    def __call__(self, path):
        with open(path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        request = vision.AnnotateImageRequest(image=image, features=self.__features)
        res = self.client.annotate_image(request)

        full_text = res.full_text_annotation.text

        annotations = res.text_annotations
        whole_text_box_max = annotations[0].bounding_poly.vertices[
            2
        ]  # slice out entire body of text
        max_width = whole_text_box_max.x
        max_height = whole_text_box_max.y

        annotations_normed = []
        for text in annotations[1:]:
            box = text.bounding_poly.vertices

            # midpoint: average position betwen
            # the upper left location and lower
            # right position
            midpoint = ((box[2].x + box[0].x) / 2, (box[2].y + box[0].y) / 2)

            annotations_normed.append(
                ImageAnnotation(
                    text=text.description,
                    midpoint=midpoint,
                    midpoint_normalized=(
                        midpoint[0] / max_width,
                        midpoint[1] / max_height,
                    ),
                )
            )

        annotations_normed = list(
            sorted(
                annotations_normed,
                key=lambda x: (x.midpoint_normalized[1], x.midpoint_normalized[0]),
            )
        )
        response = ImageAnnotatorResponse(
            full_text=full_text,
            orig_text_dims=(max_width, max_height),
            words=annotations_normed,
        )

        return response
