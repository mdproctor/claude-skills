"""
Shared regex patterns for markdown parsing.

Import these constants instead of re-defining patterns in each validator.
"""

# Standard markdown link: [text](url)
MD_LINK_PATTERN = r'\[([^\]]+)\]\(([^)]+)\)'

# HTML-style include directives: <!-- include: path -->
MD_INCLUDE_PATTERN = r'<!--\s*include:\s*([^\s]+)\s*-->'

# Section cross-references: § Section Name in file.md or (file.md)
MD_SECTION_REF_PATTERN = r'§\s+[^(]+\s+(?:in|\()\s*([^\s)]+\.md)'

# Markdown heading: # Title or ## Title etc.
MD_HEADER_PATTERN = r'^#{1,6}\s+(.+)$'
