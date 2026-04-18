"""Speaker notes template strings for different languages.

These templates are used by the content generator to create
contextual speaker notes for different slide types and languages.
"""

# Japanese speaker notes templates
SPEAKER_NOTES_JA_TITLE_SLIDE = (
    "このプレゼンテーションでは「{title}」について説明します。{content}について詳しく見ていきます。"
)

SPEAKER_NOTES_JA_SECTION_SLIDE = (
    "次のセクションでは「{title}」について説明します。{content}に焦点を当てます。"
)

SPEAKER_NOTES_JA_CONTENT_SLIDE = (
    "「{title}」に関して、{content}という点が重要です。これらの詳細について説明します。"
)

# English speaker notes templates (for completeness and future extensibility)
SPEAKER_NOTES_EN_TITLE_SLIDE = (
    "This presentation covers {title}. We will explore {content} in detail."
)

SPEAKER_NOTES_EN_SECTION_SLIDE = (
    "In this section, we will discuss {title}. The focus will be on {content}."
)

SPEAKER_NOTES_EN_CONTENT_SLIDE = (
    "Regarding {title}, the key points are: {content}. Let me elaborate on these details."
)
