"""File validation module for PPTX files."""

import re
import zipfile
from pathlib import Path

from pptx_agent.validators.exceptions import (
    CompressionRatioError,
    FileSizeLimitError,
    InvalidFileError,
    SecurityValidationError,
)
from pptx_agent.validators.security import validate_xml_safety

# Constants for validation limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB
MAX_COMPRESSION_RATIO = 100


def validate_pptx_file(file_path: Path | str) -> None:
    """Validate PPTX file against ZIP bomb and size constraints.

    Args:
        file_path: Path to the PPTX file to validate

    Raises:
        InvalidFileError: If file does not exist or is not a valid ZIP file
        FileSizeLimitError: If file size or uncompressed size exceeds limits
        CompressionRatioError: If compression ratio is suspicious

    """
    # Convert to Path object if string
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check compressed file size (EAFP pattern - try operation directly)
    try:
        file_size = file_path.stat().st_size
    except FileNotFoundError as e:
        msg = (
            f"File validation failed: file does not exist at '{file_path}'. "
            "Expected: valid path to existing file."
        )
        raise InvalidFileError(msg) from e
    if file_size > MAX_FILE_SIZE:
        msg = (
            f"File size limit exceeded: {file_size} bytes (compressed), "
            f"maximum allowed is {MAX_FILE_SIZE} bytes."
        )
        raise FileSizeLimitError(msg)

    # Try to open as ZIP file
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Calculate total uncompressed size and check compression ratio in a single loop
            total_uncompressed_size = 0

            for info in zf.infolist():
                total_uncompressed_size += info.file_size

                # Check compression ratio for each file (avoid division by zero)
                if info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > MAX_COMPRESSION_RATIO:
                        msg = (
                            f"Suspicious compression ratio detected: file '{info.filename}' has "
                            f"compression ratio of {ratio:.1f}x, maximum allowed is "
                            f"{MAX_COMPRESSION_RATIO}x. Expected: valid compression ratio."
                        )
                        raise CompressionRatioError(msg)

            # Check total uncompressed size (after gathering total)
            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                msg = (
                    f"Uncompressed size limit exceeded: {total_uncompressed_size} bytes total, "
                    f"maximum allowed is {MAX_UNCOMPRESSED_SIZE} bytes."
                )
                raise FileSizeLimitError(msg)

    except zipfile.BadZipFile as e:
        msg = f"File format validation failed: file is not a valid ZIP/PPTX file. Details: {e}"
        raise InvalidFileError(msg) from e


def validate_file_extension(file_path: Path | str) -> None:
    """Validate file has allowed extension (.pptx only).

    Args:
        file_path: Path to the file to validate

    Raises:
        InvalidFileError: If file extension is not .pptx

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Get file extension (case-insensitive)
    file_extension = file_path.suffix.lower()

    # Only allow .pptx extension
    if file_extension != ".pptx":
        msg = (
            f"File extension validation failed: '{file_extension}' is not allowed. "
            "Expected: .pptx extension only."
        )
        raise InvalidFileError(msg)


def validate_no_symlinks(file_path: Path | str) -> None:
    """Validate that file path does not contain symlinks.

    Args:
        file_path: Path to validate

    Raises:
        SecurityValidationError: If path contains symlinks

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Check if the file itself is a symlink
    if file_path.is_symlink():
        msg = (
            f"Symlink validation failed: file at '{file_path}' is a symlink. "
            "Expected: regular file without symlinks."
        )
        raise SecurityValidationError(msg)

    # Check if any parent directory is a symlink
    try:
        # Check each parent in the original path
        current = file_path.absolute()
        while current != current.parent:
            if current.is_symlink():
                msg = (
                    f"Symlink validation failed: path contains symlink at '{current}'. "
                    "Expected: regular file path without symlinks."
                )
                raise SecurityValidationError(msg)
            current = current.parent
    except (OSError, RuntimeError) as e:
        msg = f"Symlink validation failed: error while validating path. Details: {e}"
        raise SecurityValidationError(msg) from e


def validate_pptx_structure(file_path: Path | str) -> None:
    """Validate PPTX internal XML structure against malicious patterns.

    Protects against:
    - XML billion laughs attack (entity expansion)
    - XXE (external entity injection)
    - Excessive entity expansion depth

    **セキュリティ設計の判断根拠 (Code Review M-5より):**

    現在の実装は、XMLパーサーを使わず正規表現ベースの検出を採用しています。
    これはCLIツールとしての使用において以下の理由で十分です:

    1. **信頼されたファイル源**: CLIツールとして、ユーザーが明示的に指定した
       ローカルファイルのみを処理します。不特定多数からのアップロードは想定していません。

    2. **単純な検出で十分な脅威**: 正規表現で検出対象の<!ENTITY>やSYSTEMは、
       PPTXファイルの正常な構造には不要です。これらが含まれる場合は、
       明らかに異常または悪意のある改変がなされています。

    3. **エンコーディングバイパスのリスク**: UTF-16やUTF-32でエンコードされた
       <!ENTITY>を検出できない可能性がありますが、Office製品が生成する
       標準的なPPTXファイルはUTF-8を使用するため、現在の用途では許容されます。

    **将来のWebサービス化における考慮事項:**

    もしこのツールをWebサービスとして展開する場合は、以下の対策を推奨します:

    1. **defusedxmlの導入**: 正規表現ではなくdefusedxmlライブラリを使用し、
       XML解析時に自動的にXXEやエンティティ展開を防ぐことを検討してください。

    2. **エンコーディング対策**: 様々なエンコーディングでのバイパスを防ぐため、
       XMLパーサーレベルでの検証が必要になります。

    3. **サンドボックス環境**: 信頼できないファイルを隔離された環境で
       処理する仕組みを構築してください。

    Args:
        file_path: Path to the PPTX file

    Raises:
        SecurityValidationError: If malicious XML patterns detected

    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Regex-based malicious XML detection (fast pre-check for CLI use).
    # See docstring for security design rationale and future considerations.
    entity_pattern = re.compile(rb"<!ENTITY", re.IGNORECASE)
    doctype_pattern = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
    system_pattern = re.compile(rb"SYSTEM\s+", re.IGNORECASE)

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Check all XML files in the PPTX
            for file_info in zf.infolist():
                if file_info.filename.endswith(".xml") or file_info.filename.endswith(".rels"):
                    content = zf.read(file_info.filename)

                    # エンティティ宣言の検出 (Billion Laughs攻撃、エンティティ展開攻撃)
                    # 標準的なPPTXファイルには<!ENTITY>は含まれないため、
                    # これが存在する場合は悪意のある改変と判断できます。
                    # 制限事項: UTF-8以外のエンコーディングでのバイパスは検出できませんが、
                    # Office製品が生成するPPTXはUTF-8を使用するため、CLI用途では許容されます。
                    if entity_pattern.search(content):
                        msg = (
                            f"XML security validation failed: malicious entity declaration "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without entity declarations."
                        )
                        raise SecurityValidationError(msg)

                    # XXE (外部エンティティ参照) の検出
                    # <!DOCTYPE>自体は一部のXMLで正当に使用されるため、
                    # SYSTEMキーワードとの組み合わせで外部エンティティ参照を検出します。
                    # これによりファイルシステムへのアクセスやネットワークリクエストを防ぎます。
                    if doctype_pattern.search(content) and system_pattern.search(content):
                        msg = (
                            f"XML security validation failed: external entity reference (XXE) "
                            f"detected in '{file_info.filename}'. "
                            "Expected: XML without external entity references."
                        )
                        raise SecurityValidationError(msg)

                    # Defense-in-depth: validate via defusedxml parser
                    # after regex pre-checks pass.
                    try:
                        decoded_content = content.decode("utf-8")
                    except UnicodeDecodeError as e:
                        # Non-UTF-8 XML in a PPTX is suspicious
                        msg = (
                            f"XML security validation failed: unable to decode "
                            f"'{file_info.filename}' as UTF-8. "
                            "Expected: UTF-8 encoded XML."
                        )
                        raise SecurityValidationError(msg) from e

                    if not validate_xml_safety(decoded_content):
                        msg = (
                            f"XML security validation failed: defusedxml detected "
                            f"a potential threat in '{file_info.filename}'. "
                            "Expected: XML without malicious patterns."
                        )
                        raise SecurityValidationError(msg)

    except zipfile.BadZipFile as e:
        msg = (
            f"PPTX structure validation failed: cannot validate structure due to invalid "
            f"ZIP file. Details: {e}"
        )
        raise InvalidFileError(msg) from e


def validate_template_path(template_path: str) -> Path:
    """Validate template path for storage and retrieval.

    Validates that the template path:
    - Has .pptx extension
    - Does not contain symlinks
    - Exists and is a valid PPTX file
    - Has no malicious XML patterns (XXE, Billion Laughs)
    - Is readable

    Args:
        template_path: Path to the template file

    Returns:
        Absolute Path object to the validated template

    Raises:
        InvalidFileError: If file does not exist, has wrong extension, or is not a valid PPTX
        SecurityValidationError: If path contains symlinks or malicious XML patterns
            (XXE, entity expansion)
        FileSizeLimitError: If file size exceeds limits
        CompressionRatioError: If compression ratio is suspicious

    """
    # Convert to Path object
    path = Path(template_path)

    # Validate file extension first (before checking existence)
    validate_file_extension(path)

    # Check if file exists
    if not path.exists():
        msg = (
            f"Template path validation failed: file does not exist at '{template_path}'. "
            "Expected: valid path to existing template file."
        )
        raise InvalidFileError(msg)

    # Validate no symlinks
    # This provides security against symlink attacks without being overly restrictive
    # for CLI usage where users explicitly specify template paths
    validate_no_symlinks(path)

    # Validate PPTX file structure and size
    validate_pptx_file(path)

    # Validate PPTX internal XML structure (XXE, Billion Laughs protection)
    validate_pptx_structure(path)

    # Return absolute path
    return path.resolve()
