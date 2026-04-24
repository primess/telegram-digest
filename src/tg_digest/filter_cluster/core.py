import hashlib
import re
from dataclasses import dataclass

from tg_digest.types import RawMessage


@dataclass(frozen=True)
class FilterConfig:
    min_chars: int = 20
    languages: list[str] | None = None
    blacklist_keywords: list[str] | None = None
    sim_threshold: float = 0.72


@dataclass(frozen=True)
class Cluster:
    messages: list[RawMessage]
    representative: RawMessage
    traction: float


class FilterCluster:
    def __init__(self, config: FilterConfig | None = None) -> None:
        self.config = config or FilterConfig()

    def filter(self, msgs: list[RawMessage]) -> list[RawMessage]:
        seen_hashes: set[str] = set()
        kept: list[RawMessage] = []
        languages = self.config.languages or ["en", "he"]
        blacklist = [term.lower() for term in (self.config.blacklist_keywords or [])]
        for message in msgs:
            normalized = normalize_text(message.text)
            text_without_urls = strip_urls(normalized)
            if len(strip_emoji(text_without_urls).strip()) < self.config.min_chars:
                continue
            lowered = normalized.lower()
            if any(term in lowered for term in blacklist):
                continue
            if detect_language(normalized) not in languages:
                continue
            text_hash = hashlib.sha256(normalized.encode()).hexdigest()
            if text_hash in seen_hashes:
                continue
            seen_hashes.add(text_hash)
            kept.append(message)
        return kept

    def cluster(self, msgs: list[RawMessage]) -> list[Cluster]:
        clusters: list[list[RawMessage]] = []
        fingerprints: list[set[str]] = []
        for message in msgs:
            fp = shingles(message.text)
            match_index = None
            for index, existing in enumerate(fingerprints):
                if jaccard(fp, existing) >= self.config.sim_threshold:
                    match_index = index
                    break
            if match_index is None:
                clusters.append([message])
                fingerprints.append(fp)
            else:
                clusters[match_index].append(message)
                fingerprints[match_index] |= fp

        result = []
        for messages in clusters:
            representative = max(messages, key=lambda item: (len(item.text), -item.msg_id))
            result.append(
                Cluster(
                    messages=messages, representative=representative, traction=float(len(messages))
                )
            )
        return result


def normalize_text(text: str) -> str:
    no_zero_width = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    return re.sub(r"\s+", " ", no_zero_width).strip()


def strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text)


def strip_emoji(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) < 0x1F300)


def detect_language(text: str) -> str:
    if re.search(r"[\u0590-\u05FF]", text):
        return "he"
    lowered = text.lower()
    french_markers = ("ceci", "francais", "français", " marche", " marchés")
    if any(marker in lowered for marker in french_markers):
        return "fr"
    return "en"


def shingles(text: str, size: int = 3) -> set[str]:
    words = re.findall(r"[\w\u0590-\u05FF]+", normalize_text(text).lower())
    if len(words) <= size:
        return set(words)
    return {" ".join(words[index : index + size]) for index in range(len(words) - size + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
