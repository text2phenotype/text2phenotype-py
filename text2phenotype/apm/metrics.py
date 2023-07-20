import elasticapm
import functools

from elasticapm.utils import get_name_from_func

from text2phenotype.constants.apm import (
    TEXT2PHENOTYPE_TXT_LEN,
    TEXT2PHENOTYPE_TID,
    TEXT2PHENOTYPE_KEY,
    TEXT2PHENOTYPE_TOK_COUNT,
)


class text2phenotype_capture_span(elasticapm.capture_span):
    def __call__(self, func):
        self.name = self.name or get_name_from_func(func)

        @functools.wraps(func)
        def decorated(*args, **kwds):
            self.extra = self.extra or {}
            text2phenotype = self.extra.setdefault(TEXT2PHENOTYPE_KEY, {})
            text2phenotype[TEXT2PHENOTYPE_TID] = kwds.get('tid')
            with self:
                return func(*args, **kwds)

        return decorated


def text2phenotype_capture_text_info(text_length: int = None, token_count: int = None,
                            tid: str = None):
    data = {
        TEXT2PHENOTYPE_TXT_LEN: text_length,
        TEXT2PHENOTYPE_TOK_COUNT: token_count,
        TEXT2PHENOTYPE_TID: tid,
    }
    elasticapm.set_context(data, key=TEXT2PHENOTYPE_KEY)
