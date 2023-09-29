from dataclasses import dataclass,replace,field
from typing import List, Tuple, Self,Optional

from google.cloud import vision

from llama2d.constants import SCREEN_RESOLUTION, SECRETS_FILE


@dataclass
class ImageAnnotation:
    text: str  # the word
    midpoint: Tuple[float, float]  # the UNNORMALIZED midpoint of the word, (X,Y)
    midpoint_normalized: Tuple[
        float, float
    ]  # the normalized midpoint between 0 - 1  (X,Y)


@dataclass
class Llama2dScreen:
    full_text: str=""  # full text
    orig_text_dims: Tuple[
        float, float
    ]=(1.,1.)  # the dimension of the *TEXT PORTION* of the image

    words: List[ImageAnnotation]=field(default_factory=list)  # a list of words and their midpoints

    def __add__(self,other:Self)->Self:
        assert self.orig_text_dims == other.orig_text_dims
        return replace(self,words=self.words+other.words)
    
    def push_word(
            self,
            word:str,

            # must use exactly one
            # all 4 corners
            xyxy:Optional[Tuple[float,float,float,float]]=None,
            # midpoint
            xy:Optional[Tuple[float,float,float,float]]=None,
        ):
        new = self.concat_word(word=word,xyxy=xyxy,xy=xy)

        self.words = new.words
        self.full_text = new.full_text
    
    def concat_word(
        self,
        word:str,

        # must use exactly one
        # all 4 corners
        xyxy:Optional[Tuple[float,float,float,float]]=None,
        # midpoint
        xy:Optional[Tuple[float,float,float,float]]=None,

    ):
        full_text = self.full_text
        words = self.words

        if len(words) > 0:
            full_text += " "
        full_text+=word

        assert (xyxy is None) != (xy is None),"You should specify xy (midpoint) xor xyxy (corners)."
        if xy is None:
            x = (xyxy[0] + xyxy[2]) / 2
            y = (xyxy[1] + xyxy[3]) / 2
            xy = (x,y)

        x,y = xy
        w,h = self.orig_text_dims
        xy_norm = (x/w,y/h)

        new_ann = ImageAnnotation(text=word,midpoint=xy,midpoint_normalized=xy_norm)
        words = words+[new_ann]


        return replace(self,words=words,full_text=full_text)
    
    def __getitem__(self,key:slice):
        assert type(key)==slice,"__getitem__ only supports slice right now"
        words = self.words[key]

        full_text = " ".join(words)

        return replace(self,words=words,full_text=full_text)


width, height = SCREEN_RESOLUTION


class ImageAnnotator:
    def __init__(self, credentials=SECRETS_FILE):
        if not credentials.exists():
            raise ValueError(
                f"Place the Google Cloud credentials file in {credentials}"
            )

        self.client = vision.ImageAnnotatorClient.from_service_account_file(credentials)
        self.__features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]

    def __call__(self, path):
        with open(path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        request = vision.AnnotateImageRequest(image=image, features=self.__features)
        res = self.client.annotate_image(request)

        full_text = res.full_text_annotation.text

        annotations = res.text_annotations

        annotations_normed = Llama2dScreen(
            full_text=full_text,
            orig_text_dims=SCREEN_RESOLUTION,
        )
        for text in annotations[1:]:
            annotations_normed.push_word(
                word=text.description,
                xyxy=text.bounding_poly.vertices
            )

        # optionally, sort the words by midpoint
        annotations_normed.words = list(
            sorted(
                annotations_normed.words,
                key=lambda x: (x.midpoint_normalized[1], x.midpoint_normalized[0]),
            )
        )

        return annotations_normed
