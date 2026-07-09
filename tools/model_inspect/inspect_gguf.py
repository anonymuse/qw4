#!/usr/bin/env python3
"""Inspect GGUF model metadata without loading tensor payloads."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import struct
import sys
from typing import Any


GGUF_MAGIC = b"GGUF"
DEFAULT_ALIGNMENT_BYTES = 32
MAX_ARRAY_LENGTH = 10_000_000
MAX_STRING_LENGTH = 1_000_000_000
MAX_TENSOR_DIMS = 16

GGUF_VALUE_TYPES = {
    0: "uint8",
    1: "int8",
    2: "uint16",
    3: "int16",
    4: "uint32",
    5: "int32",
    6: "float32",
    7: "bool",
    8: "string",
    9: "array",
    10: "uint64",
    11: "int64",
    12: "float64",
}

GGUF_SCALAR_FORMATS = {
    0: "<B",
    1: "<b",
    2: "<H",
    3: "<h",
    4: "<I",
    5: "<i",
    6: "<f",
    7: "<?",
    10: "<Q",
    11: "<q",
    12: "<d",
}

GGML_TYPES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    6: "Q5_0",
    7: "Q5_1",
    8: "Q8_0",
    9: "Q8_1",
    10: "Q2_K",
    11: "Q3_K",
    12: "Q4_K",
    13: "Q5_K",
    14: "Q6_K",
    15: "Q8_K",
    16: "IQ2_XXS",
    17: "IQ2_XS",
    18: "IQ3_XXS",
    19: "IQ1_S",
    20: "IQ4_NL",
    21: "IQ3_S",
    22: "IQ2_S",
    23: "IQ4_XS",
    24: "I8",
    25: "I16",
    26: "I32",
    27: "I64",
    28: "F64",
    29: "IQ1_M",
    30: "BF16",
    31: "Q4_0_4_4",
    32: "Q4_0_4_8",
    33: "Q4_0_8_8",
    34: "TQ1_0",
    35: "TQ2_0",
    36: "IQ4_NL_4_4",
    37: "IQ4_NL_4_8",
    38: "IQ4_NL_8_8",
}

INTERESTING_METADATA_KEYS = (
    "general.name",
    "general.architecture",
    "general.basename",
    "general.size_label",
    "general.file_type",
    "general.quantization_version",
    "general.alignment",
    "split.count",
    "split.no",
    "split.tensors.count",
    "tokenizer.ggml.model",
    "tokenizer.ggml.tokens",
    "tokenizer.ggml.bos_token_id",
    "tokenizer.ggml.eos_token_id",
    "tokenizer.ggml.padding_token_id",
)

QWEN3_PREFIX_CANDIDATES = (
    "qwen3moe",
    "qwen3",
    "qwen2moe",
    "qwen2",
)

QWEN_SHAPE_SUFFIXES = (
    "block_count",
    "context_length",
    "embedding_length",
    "feed_forward_length",
    "attention.head_count",
    "attention.head_count_kv",
    "attention.key_length",
    "attention.value_length",
    "expert_count",
    "expert_used_count",
    "rope.freq_base",
    "rope.dimension_count",
)


class GgufError(ValueError):
    """Raised when a GGUF file cannot be parsed."""


@dataclass(frozen=True)
class TensorInfo:
    name: str
    dimensions: list[int]
    ggml_type: int
    offset: int

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dimensions": self.dimensions,
            "ggml_type": self.ggml_type,
            "ggml_type_name": GGML_TYPES.get(self.ggml_type, f"UNKNOWN_{self.ggml_type}"),
            "offset": self.offset,
        }


class Reader:
    def __init__(self, path: Path):
        self.path = path
        self.handle = path.open("rb")

    def close(self) -> None:
        self.handle.close()

    def tell(self) -> int:
        return self.handle.tell()

    def read_exact(self, size: int) -> bytes:
        data = self.handle.read(size)
        if len(data) != size:
            raise GgufError(f"{self.path}: unexpected end of file")
        return data

    def unpack(self, fmt: str) -> Any:
        data = self.read_exact(struct.calcsize(fmt))
        values = struct.unpack(fmt, data)
        if len(values) == 1:
            return values[0]
        return values

    def read_string(self) -> str:
        length = self.unpack("<Q")
        if length > MAX_STRING_LENGTH:
            raise GgufError(f"{self.path}: unreasonable string length {length}")
        data = self.read_exact(length)
        return data.decode("utf-8", errors="replace")


def parse_value(reader: Reader, value_type: int) -> Any:
    if value_type in GGUF_SCALAR_FORMATS:
        return reader.unpack(GGUF_SCALAR_FORMATS[value_type])
    if value_type == 8:
        return reader.read_string()
    if value_type == 9:
        array_type = reader.unpack("<I")
        array_len = reader.unpack("<Q")
        if array_len > MAX_ARRAY_LENGTH:
            raise GgufError(f"{reader.path}: unreasonable array length {array_len}")
        values: list[Any] = []
        keep_all_values = array_len <= 64
        sample_limit = 8
        for index in range(array_len):
            item = parse_value(reader, array_type)
            if keep_all_values or index < sample_limit:
                values.append(item)
        return {
            "array_type": GGUF_VALUE_TYPES.get(array_type, f"unknown_{array_type}"),
            "length": array_len,
            "values": values,
            "values_omitted": array_len > 64,
        }
    raise GgufError(f"{reader.path}: unsupported GGUF metadata value type {value_type}")


def metadata_alignment(metadata: dict[str, Any], path: Path) -> int:
    value = metadata.get("general.alignment", DEFAULT_ALIGNMENT_BYTES)
    if isinstance(value, bool) or not isinstance(value, int):
        raise GgufError(f"{path}: invalid general.alignment value {value!r}")
    if value <= 0 or value > 1_000_000:
        raise GgufError(f"{path}: unreasonable general.alignment value {value}")
    return value


def align_offset(offset: int, alignment: int) -> int:
    remainder = offset % alignment
    if remainder == 0:
        return offset
    return offset + alignment - remainder


def parse_gguf(path: Path, *, tensor_sample: int) -> dict[str, Any]:
    reader = Reader(path)
    try:
        magic = reader.read_exact(4)
        if magic != GGUF_MAGIC:
            raise GgufError(f"{path}: not a GGUF file")
        version = reader.unpack("<I")
        tensor_count = reader.unpack("<Q")
        metadata_kv_count = reader.unpack("<Q")

        metadata: dict[str, Any] = {}
        metadata_types: dict[str, str] = {}
        for _ in range(metadata_kv_count):
            key = reader.read_string()
            value_type = reader.unpack("<I")
            metadata_types[key] = GGUF_VALUE_TYPES.get(value_type, f"unknown_{value_type}")
            metadata[key] = parse_value(reader, value_type)

        metadata_end_bytes = reader.tell()
        tensor_type_counts: Counter[str] = Counter()
        tensor_samples: list[dict[str, Any]] = []
        last_tensors: list[dict[str, Any]] = []
        for index in range(tensor_count):
            name = reader.read_string()
            dim_count = reader.unpack("<I")
            if dim_count > MAX_TENSOR_DIMS:
                raise GgufError(f"{path}: unreasonable tensor dimension count {dim_count}")
            dimensions = [reader.unpack("<Q") for _ in range(dim_count)]
            ggml_type = reader.unpack("<I")
            offset = reader.unpack("<Q")
            tensor = TensorInfo(name=name, dimensions=dimensions, ggml_type=ggml_type, offset=offset)
            type_name = GGML_TYPES.get(ggml_type, f"UNKNOWN_{ggml_type}")
            tensor_type_counts[type_name] += 1
            tensor_json = tensor.to_json()
            if index < tensor_sample:
                tensor_samples.append(tensor_json)
            if tensor_sample > 0:
                last_tensors.append(tensor_json)
                if len(last_tensors) > tensor_sample:
                    last_tensors.pop(0)

        tensor_table_end_bytes = reader.tell()
        alignment_bytes = metadata_alignment(metadata, path)
        tensor_data_offset_bytes = align_offset(tensor_table_end_bytes, alignment_bytes)

        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "version": version,
            "tensor_count": tensor_count,
            "metadata_kv_count": metadata_kv_count,
            "metadata_header_bytes": tensor_table_end_bytes,
            "metadata_end_bytes": metadata_end_bytes,
            "tensor_table_end_bytes": tensor_table_end_bytes,
            "alignment_bytes": alignment_bytes,
            "tensor_data_offset_bytes": tensor_data_offset_bytes,
            "tensor_type_counts": dict(sorted(tensor_type_counts.items())),
            "metadata": metadata,
            "metadata_types": metadata_types,
            "tensor_samples": {
                "first": tensor_samples,
                "last": last_tensors,
            },
        }
    finally:
        reader.close()


def find_gguf_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        files = sorted(item for item in path.glob("*.gguf") if item.is_file())
        if not files:
            files = sorted(item for item in path.rglob("*.gguf") if item.is_file())
        if files:
            return files
    raise GgufError(f"{path}: no GGUF files found")


def interesting_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key in INTERESTING_METADATA_KEYS:
        if key in metadata:
            selected[key] = summarize_value(metadata[key])

    for prefix in QWEN3_PREFIX_CANDIDATES:
        for suffix in QWEN_SHAPE_SUFFIXES:
            key = f"{prefix}.{suffix}"
            if key in metadata:
                selected[key] = summarize_value(metadata[key])
    return selected


def infer_qwen_shape(metadata: dict[str, Any]) -> dict[str, Any]:
    architecture = str(metadata.get("general.architecture", ""))
    prefixes = [architecture] if architecture else []
    prefixes.extend(prefix for prefix in QWEN3_PREFIX_CANDIDATES if prefix not in prefixes)

    shape: dict[str, Any] = {}
    for prefix in prefixes:
        for suffix in QWEN_SHAPE_SUFFIXES:
            key = f"{prefix}.{suffix}"
            if key in metadata and suffix not in shape:
                shape[suffix] = summarize_value(metadata[key])
    return shape


def summarize_value(value: Any) -> Any:
    if isinstance(value, dict) and "array_type" in value and "length" in value:
        summary = {
            "array_type": value["array_type"],
            "length": value["length"],
        }
        values = value.get("values")
        if values and value["length"] <= 8:
            summary["values"] = values
        return summary
    return value


def aggregate(files: list[dict[str, Any]]) -> dict[str, Any]:
    first_metadata = files[0]["metadata"]
    type_counts: Counter[str] = Counter()
    for item in files:
        type_counts.update(item["tensor_type_counts"])
    return {
        "file_count": len(files),
        "total_size_bytes": sum(item["size_bytes"] for item in files),
        "total_tensor_count": sum(item["tensor_count"] for item in files),
        "metadata": interesting_metadata(first_metadata),
        "qwen_shape": infer_qwen_shape(first_metadata),
        "tensor_type_counts": dict(sorted(type_counts.items())),
        "files": [
            {
                "path": item["path"],
                "size_bytes": item["size_bytes"],
                "version": item["version"],
                "tensor_count": item["tensor_count"],
                "metadata_kv_count": item["metadata_kv_count"],
                "metadata_header_bytes": item["metadata_header_bytes"],
                "metadata_end_bytes": item["metadata_end_bytes"],
                "tensor_table_end_bytes": item["tensor_table_end_bytes"],
                "alignment_bytes": item["alignment_bytes"],
                "tensor_data_offset_bytes": item["tensor_data_offset_bytes"],
                "tensor_type_counts": item["tensor_type_counts"],
                "tensor_samples": item["tensor_samples"],
            }
            for item in files
        ],
    }


def format_bytes(value: int) -> str:
    gib = value / 1024**3
    gb = value / 1_000_000_000
    return f"{gb:.2f} GB ({gib:.2f} GiB)"


def format_human(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# GGUF Metadata Summary")
    lines.append("")
    lines.append(f"Files: {result['file_count']}")
    lines.append(f"Total size: {format_bytes(result['total_size_bytes'])}")
    lines.append(f"Total tensors listed: {result['total_tensor_count']}")
    lines.append("")
    lines.append("## Model Metadata")
    if result["metadata"]:
        for key, value in result["metadata"].items():
            lines.append(f"- {key}: {format_jsonish(value)}")
    else:
        lines.append("- no selected metadata keys found")
    lines.append("")
    lines.append("## Qwen Shape")
    if result["qwen_shape"]:
        for key, value in result["qwen_shape"].items():
            lines.append(f"- {key}: {format_jsonish(value)}")
    else:
        lines.append("- no Qwen shape keys found")
    lines.append("")
    lines.append("## Tensor Types")
    for key, value in result["tensor_type_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Files")
    for item in result["files"]:
        lines.append(f"- {item['path']}")
        lines.append(f"  size: {format_bytes(item['size_bytes'])}")
        lines.append(
            f"  version: {item['version']}, tensors: {item['tensor_count']}, "
            f"metadata kv: {item['metadata_kv_count']}, header bytes: {item['metadata_header_bytes']}"
        )
        lines.append(
            f"  metadata end: {item['metadata_end_bytes']}, tensor table end: "
            f"{item['tensor_table_end_bytes']}, tensor data offset: {item['tensor_data_offset_bytes']}"
        )
    return "\n".join(lines)


def format_jsonish(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect GGUF metadata and tensor tables without reading model tensor payloads."
    )
    parser.add_argument("path", help="GGUF file or directory containing GGUF files.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--tensor-sample",
        type=int,
        default=3,
        help="Number of first/last tensor table entries to include per file.",
    )
    args = parser.parse_args(argv)

    if args.tensor_sample < 0:
        print("inspect_gguf: --tensor-sample must be non-negative", file=sys.stderr)
        return 2

    try:
        paths = find_gguf_files(Path(args.path))
        files = [parse_gguf(path, tensor_sample=args.tensor_sample) for path in paths]
        result = aggregate(files)
    except (OSError, GgufError, UnicodeDecodeError, struct.error) as exc:
        print(f"inspect_gguf: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_human(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
