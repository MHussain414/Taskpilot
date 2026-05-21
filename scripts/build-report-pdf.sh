#!/usr/bin/env bash
# Build TaskPilot_Report.pdf using pdflatex (WSL Kali / Linux)
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$PROJECT/docs/report"

cd "$REPORT_DIR"
rm -f TaskPilot_Report.aux TaskPilot_Report.log TaskPilot_Report.toc TaskPilot_Report.out

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "[*] Installing TeX Live..."
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra \
    texlive-fonts-recommended texlive-fonts-extra texlive-fonts-lmodern \
    texlive-pictures texlive-science texlive-humanities \
    texlive-fontawesome5
fi

echo "[*] pdflatex pass 1..."
pdflatex -interaction=nonstopmode -halt-on-error TaskPilot_Report.tex >/dev/null
echo "[*] pdflatex pass 2..."
pdflatex -interaction=nonstopmode -halt-on-error TaskPilot_Report.tex >/dev/null

cp -f TaskPilot_Report.pdf "$PROJECT/TaskPilot_Report.pdf"
echo "[+] PDF: $PROJECT/TaskPilot_Report.pdf"
ls -lh "$PROJECT/TaskPilot_Report.pdf"
