# Focused discovery follow-up — 2026-09-12

After the wheel model failed the sampled cockpit preview, additional searches targeted `F1 tire wheel segmentation dataset roboflow`, `Formula 1 track boundary segmentation dataset github`, `site:universe.roboflow.com "f1" "tire"`, and `site:huggingface.co/datasets "Formula" "segmentation"`.

The results did not establish an accessible F1 contact-keypoint/legal-boundary dataset. Negative search results are not proof that none exists.

[wheels-tires-body](https://universe.roboflow.com/wheeltirebody/wheels-tires-body) is an additional segmentation candidate: the publisher lists 375 images, eight versions and CC BY 4.0. Version 8 lists 1,007 derivative images and a mixture of named and numeric classes. No project description establishes F1 provenance. Its published metrics are not measurements from this application and are not reused as such. No source video was uploaded for remote inference.

[TUM racetrack database](https://github.com/TUMFTM/racetrack-database) remains useful for simulation reference, with centerlines, widths and racing lines; it does not replace video-specific legal-area labels.
