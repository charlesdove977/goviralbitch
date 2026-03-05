#!/usr/bin/env python3
"""Generate PDF lead magnet from a Viral Command script.

Usage:
    python3 scripts/generate-pdf.py --script-id script_20260304_001
    python3 scripts/generate-pdf.py --script-id script_20260304_001 --brain data/agent-brain.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
    )
except ImportError:
    print("Error: reportlab not installed. Run: pip install reportlab>=4.0.0")
    sys.exit(1)


def find_script(script_id: str, scripts_path: str) -> dict | None:
    """Find a script by ID in the JSONL file."""
    if not os.path.exists(scripts_path):
        return None
    with open(scripts_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("id") == script_id:
                    return obj
            except json.JSONDecodeError:
                continue
    return None


def load_brain(brain_path: str) -> dict:
    """Load the agent brain JSON."""
    with open(brain_path, "r") as f:
        return json.load(f)


def extract_longform_content(script: dict) -> list[dict]:
    """Extract key takeaways from a longform script."""
    structure = script.get("script_structure", {})
    sections = structure.get("sections", [])
    items = []
    for i, section in enumerate(sections, 1):
        title = section.get("title", f"Step {i}")
        points = section.get("talking_points", [])
        summary = points[0] if points else ""
        proof = section.get("proof_element", "")
        items.append({"title": title, "summary": summary, "proof": proof})
    return items


def extract_shortform_content(script: dict) -> list[dict]:
    """Extract action steps from a shortform script."""
    structure = script.get("shortform_structure", {})
    beats = structure.get("beats", [])
    items = []
    for beat in beats:
        action = beat.get("action", "")
        if action:
            items.append({
                "title": f"Beat {beat.get('beat_number', '?')}",
                "summary": action,
                "proof": ""
            })
    return items


def build_pdf(script: dict, brain: dict, output_path: str):
    """Generate the PDF lead magnet."""
    # Extract creator info
    identity = brain.get("identity", {})
    creator_name = identity.get("name", "Creator")
    creator_handle = identity.get("social_handles", {}).get("youtube", "")
    if not creator_handle:
        creator_handle = identity.get("social_handles", {}).get("instagram", "")

    monetization = brain.get("monetization", {})
    cta_strategy = monetization.get("cta_strategy", {})
    funnel_url = (
        cta_strategy.get("community_url")
        or cta_strategy.get("lead_magnet_url")
        or cta_strategy.get("website_url")
        or ""
    )
    default_cta = cta_strategy.get("default_cta", "Join our community for more")

    # Script metadata
    title = script.get("title", "Content Guide")
    platform = script.get("platform", "unknown")
    is_longform = platform == "youtube_longform"

    # Extract content
    if is_longform:
        content_items = extract_longform_content(script)
        subtitle = "Video Guide & Key Takeaways"
    else:
        content_items = extract_shortform_content(script)
        subtitle = "Quick Framework & Action Steps"

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PDFTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="PDFSubtitle",
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=HexColor("#666666"),
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="CreatorLine",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=HexColor("#999999"),
        spaceAfter=30,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=16,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SectionBody",
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ProofText",
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=HexColor("#555555"),
        leftIndent=20,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CTAHead",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        spaceBefore=40,
        spaceAfter=20,
        alignment=1,  # center
    ))
    styles.add(ParagraphStyle(
        name="CTABody",
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        spaceAfter=12,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="CTAUrl",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=HexColor("#10b981"),
        spaceAfter=30,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=HexColor("#BBBBBB"),
        alignment=1,
    ))

    # Build document
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    story = []

    # Page 1: Content
    creator_line = creator_name
    if creator_handle:
        creator_line += f"  |  @{creator_handle}"

    story.append(Paragraph(creator_line, styles["CreatorLine"]))
    story.append(Paragraph(title, styles["PDFTitle"]))
    story.append(Paragraph(subtitle, styles["PDFSubtitle"]))
    story.append(HRFlowable(
        width="100%", thickness=1, color=HexColor("#DDDDDD"), spaceAfter=20
    ))

    # Content items
    for i, item in enumerate(content_items, 1):
        heading = f"{i}. {item['title']}"
        story.append(Paragraph(heading, styles["SectionHead"]))
        if item["summary"]:
            story.append(Paragraph(item["summary"], styles["SectionBody"]))
        if item.get("proof"):
            story.append(Paragraph(f"→ {item['proof']}", styles["ProofText"]))

    # Page 2: CTA
    story.append(PageBreak())
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Want to go deeper?", styles["CTAHead"]))
    story.append(Paragraph(default_cta, styles["CTABody"]))
    if funnel_url:
        story.append(Paragraph(funnel_url, styles["CTAUrl"]))

    # Social handles
    handles = identity.get("social_handles", {})
    handle_parts = []
    for platform_name, handle in handles.items():
        if handle:
            handle_parts.append(f"{platform_name}: @{handle}")
    if handle_parts:
        story.append(Paragraph("  |  ".join(handle_parts), styles["CTABody"]))

    story.append(Spacer(1, 1 * inch))
    story.append(HRFlowable(
        width="50%", thickness=0.5, color=HexColor("#DDDDDD"), spaceAfter=10
    ))
    story.append(Paragraph("Generated by Viral Command", styles["Footer"]))

    doc.build(story)


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF lead magnet from a Viral Command script"
    )
    parser.add_argument(
        "--script-id", required=True,
        help="Script ID to convert (e.g., script_20260304_001)"
    )
    parser.add_argument(
        "--brain", default="data/agent-brain.json",
        help="Path to agent-brain.json (default: data/agent-brain.json)"
    )
    parser.add_argument(
        "--scripts", default="data/scripts.jsonl",
        help="Path to scripts.jsonl (default: data/scripts.jsonl)"
    )
    parser.add_argument(
        "--output-dir", default="data/pdfs",
        help="Output directory for PDFs (default: data/pdfs)"
    )
    args = parser.parse_args()

    # Resolve paths relative to script location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_path = os.path.join(base_dir, args.scripts)
    brain_path = os.path.join(base_dir, args.brain)
    output_dir = os.path.join(base_dir, args.output_dir)

    # Find script
    script = find_script(args.script_id, scripts_path)
    if not script:
        print(f"Error: Script '{args.script_id}' not found in {scripts_path}")
        sys.exit(1)

    # Load brain
    if not os.path.exists(brain_path):
        print(f"Error: Agent brain not found at {brain_path}")
        sys.exit(1)
    brain = load_brain(brain_path)

    # Generate PDF
    output_path = os.path.join(output_dir, f"{args.script_id}.pdf")
    try:
        build_pdf(script, brain, output_path)
        print(output_path)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
