# Deck JSON specification

The root object requires a nonempty `slides` array and may include `title`. All values inside a slide remain editable in the generated PPTX. Supported slide objects:

- `{"type":"title","title":"...","subtitle":"..."}`
- `{"type":"section","title":"...","subtitle":"..."}`
- `{"type":"bullets","title":"...","bullets":["...","..."]}` — one to five bullets.
- `{"type":"two-column","title":"...","left":{"heading":"...","body":"..."},"right":{"heading":"...","body":"..."}}`
- `{"type":"metric","title":"...","value":"...","label":"...","note":"..."}`

Keep titles and bullets short enough for 16:9 slides. Review the rendered file after generation. Use native PowerPoint or another slide tool for complex plots, images, tables, and custom charts while preserving the profile colors and fonts.
