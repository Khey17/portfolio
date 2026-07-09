#!/usr/bin/env bash
# Compile assets/rendercv/resume.tex to the site CV PDF.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RENDERCV_DIR="$ROOT/assets/rendercv"
OUTPUT_DIR="$RENDERCV_DIR/rendercv_output"
BUILD_TEX="$OUTPUT_DIR/resume_build.tex"
OUTPUT_PDF="$OUTPUT_DIR/Karthikheyaa_Kurra_CV.pdf"

mkdir -p "$OUTPUT_DIR"

# glyphtounicode is pdftex-only; strip it for tectonic/xelatex builds.
sed 's/\\input{glyphtounicode}//;s/\\pdfgentounicode=1//' \
  "$RENDERCV_DIR/resume.tex" > "$BUILD_TEX"

if command -v pdflatex >/dev/null 2>&1; then
  (
    cd "$OUTPUT_DIR"
    pdflatex -interaction=nonstopmode resume_build.tex >/dev/null
    pdflatex -interaction=nonstopmode resume_build.tex >/dev/null
    cp resume_build.pdf Karthikheyaa_Kurra_CV.pdf
  )
elif command -v tectonic >/dev/null 2>&1; then
  tectonic -X compile "$BUILD_TEX" --outdir "$OUTPUT_DIR" >/dev/null
  cp "$OUTPUT_DIR/resume_build.pdf" "$OUTPUT_PDF"
else
  echo "error: install pdflatex (TeX Live) or tectonic to compile the CV" >&2
  exit 1
fi

echo "Wrote $OUTPUT_PDF"
