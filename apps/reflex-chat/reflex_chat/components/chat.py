import reflex as rx
from reflex.constants.colors import ColorType

from typing import cast
from collections.abc import Sequence

from rag_facile.pipelines import get_accepted_mime_types
from reflex_chat.state import NEGATIVE_TAGS, POSITIVE_TAGS, QA, State


def _get_upload_accept() -> dict[str, Sequence[str]]:
    """Get accepted MIME types for the file upload component."""
    return cast(dict[str, Sequence[str]], get_accepted_mime_types())


def message_content(text: str, color: ColorType) -> rx.Component:
    """Create a message content component.

    Args:
        text: The text to display.
        color: The color of the message.

    Returns:
        A component displaying the message.
    """
    return rx.markdown(
        text,
        background_color=rx.color(color, 4),
        color=rx.color(color, 12),
        display="inline-block",
        padding_inline="1em",
        border_radius="8px",
    )


def message(qa: QA) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
    return rx.box(
        rx.box(
            message_content(qa["question"], "mauve"),
            text_align="right",
            margin_bottom="8px",
        ),
        rx.box(
            message_content(qa["answer"], "accent"),
            text_align="left",
            margin_bottom="8px",
        ),
        max_width="50em",
        margin_inline="auto",
    )


def star_button(i: int) -> rx.Component:
    """A single star in the rating row."""
    return rx.icon_button(
        rx.icon(
            rx.cond(State.feedback_star >= i, "star", "star"),
            size=18,
            color=rx.cond(
                State.feedback_star >= i,
                rx.color("yellow", 9),
                rx.color("mauve", 8),
            ),
        ),
        variant="ghost",
        on_click=State.set_feedback_star(i),
        cursor="pointer",
        size="1",
    )


def tag_chip(tag: str) -> rx.Component:
    """A toggleable quality tag chip."""
    is_selected = State.feedback_tags.contains(tag)
    return rx.badge(
        tag,
        variant=rx.cond(is_selected, "solid", "outline"),
        color_scheme=rx.cond(
            State.feedback_sentiment == "positive",
            rx.cond(is_selected, "green", "gray"),
            rx.cond(is_selected, "red", "gray"),
        ),
        cursor="pointer",
        on_click=State.toggle_feedback_tag(tag),
        size="1",
    )


def feedback_panel() -> rx.Component:
    """Collapsible user feedback panel shown after each answer."""
    return rx.cond(
        State.feedback_visible,
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        "Comment évaluez-vous la réponse ?",
                        font_size="0.9em",
                        font_weight="600",
                        color=rx.color("mauve", 12),
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("chevron-up", size=14),
                        variant="ghost",
                        size="1",
                        on_click=State.dismiss_feedback,
                        cursor="pointer",
                        color=rx.color("mauve", 10),
                    ),
                    width="100%",
                    align_items="center",
                ),
                # Star rating row
                rx.hstack(
                    star_button(1),
                    star_button(2),
                    star_button(3),
                    star_button(4),
                    star_button(5),
                    spacing="1",
                ),
                # Thumbs up/down row
                rx.hstack(
                    rx.icon_button(
                        rx.icon("thumbs-up", size=16),
                        variant=rx.cond(
                            State.feedback_sentiment == "positive", "solid", "soft"
                        ),
                        color_scheme=rx.cond(
                            State.feedback_sentiment == "positive", "green", "gray"
                        ),
                        on_click=State.set_feedback_sentiment("positive"),
                        cursor="pointer",
                        size="2",
                    ),
                    rx.flex(
                        rx.foreach(
                            POSITIVE_TAGS,
                            lambda t: rx.cond(
                                State.feedback_sentiment == "positive",
                                tag_chip(t),
                                rx.fragment(),
                            ),
                        ),
                        wrap="wrap",
                        gap="1",
                    ),
                    spacing="2",
                    align_items="flex-start",
                    width="100%",
                ),
                rx.hstack(
                    rx.icon_button(
                        rx.icon("thumbs-down", size=16),
                        variant=rx.cond(
                            State.feedback_sentiment == "negative", "solid", "soft"
                        ),
                        color_scheme=rx.cond(
                            State.feedback_sentiment == "negative", "red", "gray"
                        ),
                        on_click=State.set_feedback_sentiment("negative"),
                        cursor="pointer",
                        size="2",
                    ),
                    rx.flex(
                        rx.foreach(
                            NEGATIVE_TAGS,
                            lambda t: rx.cond(
                                State.feedback_sentiment == "negative",
                                tag_chip(t),
                                rx.fragment(),
                            ),
                        ),
                        wrap="wrap",
                        gap="1",
                    ),
                    spacing="2",
                    align_items="flex-start",
                    width="100%",
                ),
                # Comment field
                rx.vstack(
                    rx.text(
                        "Commentaires",
                        font_size="0.8em",
                        color=rx.color("mauve", 11),
                    ),
                    rx.text_area(
                        placeholder="Entrez vos commentaires",
                        value=State.feedback_comment,
                        on_change=State.set_feedback_comment,
                        width="100%",
                        rows="3",
                        resize="none",
                        font_size="0.85em",
                        border_color=rx.color("mauve", 6),
                        border_radius="6px",
                    ),
                    width="100%",
                    spacing="1",
                ),
                # Submit button
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Enregistrer",
                        on_click=State.submit_feedback,
                        color_scheme="blue",
                        size="2",
                        cursor="pointer",
                    ),
                    width="100%",
                ),
                spacing="3",
                width="100%",
                padding="16px",
            ),
            max_width="50em",
            margin_inline="auto",
            margin_block="8px",
            border="1px solid var(--gray-a5)",
            border_radius="12px",
            background_color=rx.color("mauve", 2),
        ),
    )


def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.auto_scroll(
        rx.foreach(State.selected_chat, message),
        rx.cond(State.feedback_visible, feedback_panel()),
        flex="1",
        padding="8px",
    )


def render_attached_file(filename: str) -> rx.Component:
    """Render a single attached file."""
    return rx.hstack(
        rx.icon("file-text", size=14, color=rx.color("ruby", 11)),
        rx.text(
            filename, font_size="0.75em", color=rx.color("mauve", 12), weight="medium"
        ),
        rx.icon(
            "x",
            size=14,
            on_click=State.clear_attachment(filename),
            cursor="pointer",
            color=rx.color("mauve", 11),
            _hover={"color": rx.color("mauve", 12)},
        ),
        align_items="center",
        padding="6px 10px",
        border="1px solid var(--gray-a4)",
        border_radius="8px",
        background_color=rx.color("mauve", 3),
        spacing="2",
    )


def collection_badge(item: dict[str, str]) -> rx.Component:
    """Render a single collection toggle badge.

    Args:
        item: A dictionary with collection info: {id, name, enabled}.
    """
    col_id = item["id"]
    name = item["name"]
    is_active = item["enabled"] == "True"
    return rx.badge(
        rx.icon("database", size=12),
        name,
        variant=rx.cond(is_active, "solid", "outline"),
        color_scheme=rx.cond(is_active, "green", "gray"),
        cursor="pointer",
        on_click=State.toggle_collection(col_id),
        size="1",
    )


def collection_badges() -> rx.Component:
    """Render toggle badges for configured collections."""
    return rx.cond(
        State.collection_items,
        rx.flex(
            rx.text(
                "📚",
                font_size="0.75em",
                color=rx.color("mauve", 10),
            ),
            rx.foreach(State.collection_items, collection_badge),
            wrap="wrap",
            gap="2",
            align_items="center",
            padding="4px 12px",
        ),
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            collection_badges(),
            rx.form(
                rx.vstack(
                    rx.cond(
                        State.attached_files,
                        rx.flex(
                            rx.foreach(State.attached_files, render_attached_file),
                            wrap="wrap",
                            gap="2",
                            padding="8px 12px 0 12px",
                            width="100%",
                        ),
                    ),
                    rx.hstack(
                        rx.upload(
                            rx.icon("paperclip", size=18, color=rx.color("mauve", 11)),
                            id="upload_file",
                            accept=_get_upload_accept(),
                            multiple=False,
                            on_drop=State.handle_upload,
                            padding="4px",
                            cursor="pointer",
                            _hover={
                                "background_color": rx.color("mauve", 3),
                                "border_radius": "4px",
                            },
                        ),
                        rx.input(
                            placeholder="Type a message...",
                            id="question",
                            width="100%",
                            variant="soft",
                            background_color="transparent",
                            outline="none",
                            border="none",
                            _focus={
                                "box_shadow": "none",
                                "background_color": "transparent",
                            },
                        ),
                        rx.button(
                            rx.icon("send-horizontal", size=18),
                            size="2",
                            variant="ghost",
                            color_scheme="gray",
                            loading=State.processing,
                            disabled=State.processing,
                            type="submit",
                            cursor="pointer",
                        ),
                        align_items="center",
                        width="100%",
                        padding="8px 12px",
                        spacing="2",
                    ),
                    background_color=rx.color("mauve", 1),
                    border="1px solid var(--gray-a6)",
                    border_radius="12px",
                    width="100%",
                    spacing="0",
                    align_items="stretch",
                    box_shadow="0 2px 10px var(--black-a1)",
                ),
                width="100%",
                max_width="50em",
                margin_inline="auto",
                reset_on_submit=True,
                on_submit=State.process_question,
            ),
            rx.text(
                "ReflexGPT may return factually incorrect or misleading "
                "responses. Use discretion.",
                text_align="center",
                font_size=".75em",
                color=rx.color("mauve", 10),
            ),
            rx.logo(margin_block="-1em"),
            width="100%",
            padding_x="16px",
            align="stretch",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align="stretch",
        width="100%",
    )
