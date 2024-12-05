# -*- coding: utf-8 -*-
"""ELM Ordinance state extraction logic."""
import logging

logger = logging.getLogger(__name__)


class StateExtractor:
    """Helper class to extract state info from document."""

    SYSTEM_MESSAGE = (
        "You are a legal scholar that reads ordinance text and extracts "
        "state information, we want to identify the US state that the "
        "oridance applies to. Return your answer in JSON format (not "
        "markdown). Your JSON file must include exactly four keys. The first "
        "key is 'explanation', which contains a short summary of the most "
        "relevant state information you found in the text. The second key is "
        "'state', which should contain the state mentioned in the ordinance "
        "if that information cannot be found in the text. If the information "
        "cannot be found in the text the values of states should be null."
    )

    def __init__(self, structured_llm_caller):
        """

        Parameters
        ----------
        structured_llm_caller : elm.ords.llm.StructuredLLMCaller
            StructuredLLMCaller instance. Used for structured validation
            queries.
        """
        self.slc = structured_llm_caller

    async def parse(self, doc):
        """Extract state from doc.

        Parameters
        ----------
        doc : elm.web.document.BaseDocument
            Document with a `raw_pages` attribute.

        Returns
        -------
        str
        """
        results = []
        if not doc.raw_pages:
            return None

        for text in doc.raw_pages:
            if not text:
                continue

            response = await self.slc.call(
                sys_msg=self.SYSTEM_MESSAGE,
                content=f"Please extract the location or state for this ordinance:\n{text}",
                usage_sub_label="state_extraction",
            )
            if not response:
                continue
            results.append(response)

        state = {x['state'] for x in results if x['state']}   

        return state


def _parse_date(json_list):
    """Parse all date elements."""
    year = _parse_date_element(
        json_list,
        key="year",
        max_len=4,
        min_val=2000,
        max_val=float("inf"),
    )
    month = _parse_date_element(
        json_list, key="month", max_len=2, min_val=1, max_val=12
    )
    day = _parse_date_element(
        json_list, key="day", max_len=2, min_val=1, max_val=31
    )

    return year, month, day


def _parse_date_element(json_list, key, max_len, min_val, max_val):
    """Parse out a single date element."""
    date_elements = [info.get(key) for info in json_list]
    logger.debug(f"{key=}, {date_elements=}")
    date_elements = [
        int(y)
        for y in date_elements
        if y is not None
        and len(str(y)) <= max_len
        and (min_val <= int(y) <= max_val)
    ]
    if not date_elements:
        return -1 * float("inf")
    return max(date_elements)
