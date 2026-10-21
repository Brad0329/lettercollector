"""Data models for cursive script collection and storage."""
from typing import Optional
from pydantic import BaseModel, Field


class CursiveItem(BaseModel):
    """Metadata for a single cursive script image."""
    index: int = Field(description="1-based index within the character's collection")
    calligrapher: str = Field(description="Original calligrapher name (Chinese)")
    calligrapher_ko: str = Field(description="Korean pronunciation of the calligrapher name")
    url: str = Field(description="Remote source URL from sf.zdic.net")
    filename: str = Field(description="Local file name e.g. 001_황정견.gif")
    file_path: str = Field(description="Absolute local file path to the image")


class CursiveCharIndex(BaseModel):
    """Collection index metadata for a single Chinese character."""
    char: str = Field(description="Queried Chinese character")
    canonical_char: str = Field(description="Canonical character or key representing this collection")
    canonical_path: str = Field(default="", description="zdic gsft path key e.g. 1122/248309")
    total_count: int = Field(description="Total number of cursive script images")
    calligrapher_counts: dict[str, int] = Field(default_factory=dict, description="Image count per calligrapher")
    fetched_at: str = Field(description="ISO 8601 timestamp when data was fetched")
    storage_dir: str = Field(description="Absolute path to the character's storage folder")
    items: list[CursiveItem] = Field(default_factory=list, description="List of individual cursive images")
    grid_image_path: Optional[str] = Field(default=None, description="Path to generated grid preview image")
    gallery_html_path: Optional[str] = Field(default=None, description="Path to generated HTML gallery file")
