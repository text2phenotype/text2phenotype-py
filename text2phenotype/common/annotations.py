from typing import NamedTuple, Set


class AnnotationLabelConfig(NamedTuple):
    color: str  # hex value of the default color for this label
    column_index: int # IMMUTABLE integer value identifying index of this label in Biomed arrays,
    label: str  # human-readable/annotator-friendly label that will appear in annotation tool
    order: int  # default order for label in annotation tool
    persistent_label: str  # IMMUTABLE: persistent label for matching in SANDS
    visibility: bool  # whether or not label should be visible to annotators by default
    alternative_text_labels: Set[str] = set() # OPTIONAL

    def to_dict(self) -> dict:
        result = {
            'color': self.color,
            'column_index': self.column_index,
            'label': self.label,
            'order': self.order,
            'persistent_label': self.persistent_label,
            'visibility': self.visibility,
        }
        return result


class AnnotationCategoryConfig:
    """
    This class represents a single annotation labels category.  It is meant to
    be the interface between the annotation labels defined in Feature Service
    and those used by the Annotation Tool in Text2phenotype App.  It is critical that
    both Biomed/Feature Service and Annotation Tool have the same source of
    truth for these labels.

    This class and its functionality rely on the Enum values of the Feature
    Service class being of the AnnotationLabelConfig (namedtuple) type.
    
    Example implementation:
   
    class SampleCategoryVegetable(Enum):
        # column_index and persistent_label values must be unique within a category and are IMMUTABLE once defined
        NA = AnnotationLabelConfig(color='#ffffff', column_index=0, label='N/A', visibility=False, order=999, persistent_label='na')
        CARROT = AnnotationLabelConfig(color='#ffa600', column_index=1, label='Carrot', visibility=True, order=1, persistent_label='carrot')
        SNAP_PEA = AnnotationLabelConfig(color='#438f47', column_index=2, label='Snap Pea', visibility=True, order=0, persistent_label='snap_pea')
        EGGPLANT = AnnotationLabelConfig(color='#6a2191', column_index=3, label='Eggplant', visibility=True, order=2, persistent_label='eggplant')

        @classmethod
        def get_annotation_label(cls):
            return AnnotationLabelConfig(label='Vegetable',
                                         persistent_label='vegetable',  # IMMUTABLE
                                         color='#0dff00',  # Neon Green
                                         visibility=True,  # Will show in Annotator mode AND in Regular mode BY DEFAULT.
                                         # Category-level visibility affects only the behavior of SANDS in "Regular" mode.
                                         column_index=None,  # meaningless at category level
                                         order=7,  # relative order for category to appear in annotation tool
                                         )
        @classmethod
        def to_dict(cls):
            # Get JSON-compatible dictionary for HTTP response
            res_cat = AnnotationCategoryConfig(category_label=cls.get_annotation_label(),
                                               label_enum=cls)
            return res_cat.to_dict()


    # Data for HTTP Response
    data = json.dumps(SampleCategoryVegetable.to_dict())

    # See text2phenotype-py/tests/common/test_annotation_label_interfaces.py for more details
    """
    LABELS = 'labels'
    CAT_LABEL = 'category_label'

    def __init__(self, category_label: AnnotationLabelConfig, label_enum: '_LabelEnum' = None):
        self.category_label = category_label

        self.labels = []
        if label_enum:
            self.labels = [x.value for x in label_enum]

    def to_dict(self) -> dict:
        result = dict()
        result[self.CAT_LABEL] = self.category_label.to_dict()

        label_list = result.setdefault(self.LABELS, [])
        for label in self.labels:
            label_list.append(label.to_dict())

        return result

    @property
    def column_index(self):
        return self.category_label.column_index

    @property
    def label(self):
        return self.category_label.label

    @property
    def persistent_label(self):
        return self.category_label.persistent_label

    @property
    def color(self):
        return self.category_label.color

    @property
    def visibility(self):
        return self.category_label.visibility

    @property
    def order(self):
        return self.category_label.order

    @classmethod
    def from_dict(cls, data: dict) -> 'AnnotationCategoryConfig':
        inst = cls(category_label=AnnotationLabelConfig(**data[cls.CAT_LABEL]))

        label_dicts = data.get(cls.LABELS, [])
        for lab in label_dicts:
            inst.labels.append(AnnotationLabelConfig(**lab))

        return inst
