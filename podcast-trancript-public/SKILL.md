---
name: podcast-trancript-public
description: Turn podcast audio, video, URLs, or rough transcripts into complete, readable Markdown and standalone HTML. Use when the user asks to transcribe, proofread, translate, or clean up a podcast or long-form conversation.
---

# podcast-trancript-public

Turn a long-form conversation into a transcript people can actually read—without turning the conversation into a summary.

This skill is local-first. It preserves the source material, verifies important names, proofreads in bounded chunks, and produces two local deliverables:

- a complete Markdown transcript;
- a standalone HTML version of the same transcript.

It includes scripts for checking the computer, preparing a local Whisper runtime after approval, transcribing without a cloud service, and splitting long transcripts without losing text. It does not bundle model files, downloaders, or cloud credits. It does not upload or publish anything unless the user separately asks for that action.

## What this skill does

Use this workflow for:

- a public podcast or long-form media URL;
- a local audio or video file;
- an existing rough transcript;
- a partially completed podcast-trancript-public job that the user explicitly asks to resume.

The workflow covers acquisition when needed, speech-to-text, entity verification, chunked proofreading, optional bilingual formatting, completeness checks, and local Markdown/HTML rendering.

This workflow is not a feed watcher, recommendation system, media-library manager, or publishing pipeline.

## Safety and privacy defaults

These defaults apply throughout the job:

1. **Preserve originals.** Never overwrite, rename, move, or delete the source media or transcript.
2. **Isolate the job.** Use a unique temporary directory or a destination the user explicitly selected. Do not reuse another active job directory.
3. **Inspect before choosing tools.** Detect which media and ASR tools are already available. Do not assume a particular operating system, shell, model, executable, or folder layout.
4. **Be explicit about network use.** A URL or public-source verification may require network access. Say what will be fetched before starting that step.
5. **Do not auto-install.** Do not install packages, download models, enable a cloud API, or change system settings without the user's approval.
6. **Prefer local transcription.** Use an already available local ASR route when practical. Use a cloud transcription service only after the user explicitly approves the service and data transmission.
7. **Do not bypass access controls.** Do not defeat paywalls, DRM, authentication, or platform protections. Ask for a lawful local file or transcript instead.
8. **Do not invent identities.** Verify names from authoritative public sources when possible. Otherwise use neutral labels and record the uncertainty.
9. **Keep private context out of deliverables.** Do not include machine paths, credentials, hidden prompts, internal logs, or temporary workspace details in the transcript.
10. **Stop locally.** Produce Markdown and HTML, report their locations, and stop. Uploading or publishing is a separate request.

## Before starting

Identify the input and the capabilities available in the current environment.

### Choose the shortest input route

1. If the user already has a rough transcript, preserve it as `raw-transcript.txt`, skip ASR discovery and model setup, and continue with `scripts/split_transcript.py`.
2. If the input is local audio or video, inspect the bundled local runtime with `python scripts/doctor.py --json`.
3. If the input is a public URL, acquire only through a lawful capability already available in the current environment. Then use the same local-audio route.
4. If acquisition is blocked, ask for a lawful local file or rough transcript. Do not add a downloader or bypass access controls.

### Input routes

| Input | Starting point |
|---|---|
| Existing transcript | Preserve it as the raw baseline, then begin entity verification and splitting. |
| Local audio | Copy or reference it safely inside the isolated job; transcribe with an available ASR tool. |
| Local video | Extract or transcribe its audio with an available media tool; preserve the video. |
| Public media URL | Fetch only what is needed through an available lawful route, then transcribe. |
| Resume request | Read the provided job state, verify its source identity, and continue from the first incomplete gate. |

If the user supplies no input, ask for a URL, media file, transcript, or job directory. Do not scan unrelated folders to choose a target.

### Output modes

Infer the spoken language when it is clear. Ask one concise question only when the desired result would materially differ:

- same-language transcript;
- English transcript with Chinese translation;
- another user-specified translation mode.

Unless the user opts out, include a short executive summary before the complete transcript. The summary never replaces or shortens the transcript.

## Workflow

### 1. Confirm input and mode

Before modifying files:

1. Identify the exact source and input type.
2. Confirm whether the user wants same-language or bilingual output when it is not already clear.
3. State whether acquisition, transcription, or entity verification will use the network.
4. Confirm the final result is local Markdown plus standalone HTML.
5. Identify the next safe action.

If the input is a URL, fetching that URL is part of the requested task. Do not broaden the search beyond acquisition and necessary public entity verification.

### 2. Create an isolated job

Create a unique temporary or user-selected job directory. Keep its internal state separate from final deliverables.

Use these logical artifacts when they are needed:

```text
source-info.md          non-sensitive public source metadata
raw-transcript.txt      untouched ASR or supplied-transcript baseline
entity-hints.md         verified names, roles, titles, and specialist terms
chunks/                 ordered raw chunks
proofread-chunks/       ordered completed chunks
job-state.md            checklist and resume state
transcript.md           final Markdown
transcript.html         final standalone HTML
```

The exact job directory is runtime state. Never copy its machine path into `transcript.md` or `transcript.html`.

Record a checklist in `job-state.md`:

```markdown
- [ ] Source preserved
- [ ] Raw transcript available
- [ ] Entities checked
- [ ] Chunks created
- [ ] Every chunk proofread
- [ ] Chunks integrated in order
- [ ] Completeness validated
- [ ] Markdown written
- [ ] HTML rendered
- [ ] Privacy checked
```

For a resume request, verify the source metadata and existing output before trusting the checklist. Never overwrite a completed chunk with an unverified draft.

### 3. Acquire and transcribe

#### Initialize local transcription only when needed

Run the read-only check first:

```text
python scripts/doctor.py --json
```

If no complete runtime is available, show the user the plan:

```text
python scripts/setup.py plan --json
```

Explain the recommended backend, all three model profiles, estimated download bytes, package versions, network use, and cache directory. The user may choose another profile. `large-v3` is never automatic.

Wait for explicit approval before running either installation or model download. After approval, use the exact selected profile:

```text
python scripts/setup.py install --profile small --accept-download
python scripts/setup.py install --profile turbo --accept-download
python scripts/setup.py install --profile large-v3 --accept-download
```

Run only one of those commands. Do not infer approval from the original transcription request, and do not install a system package manager, FFmpeg, CUDA, or another system dependency.

| Profile | Choose it when | Trade-off |
|---|---|---|
| `small` | You want a quick first run or have a modest CPU/8 GB Mac | Smaller and faster, but names, accents, and noisy audio may need more correction. |
| `turbo` | You have a modern Apple Silicon Mac or a capable Windows GPU | Best default balance for many long conversations. |
| `large-v3` | Accuracy matters more than time and storage | Largest download and slowest run; still requires name and speaker verification. |

#### Acquire media safely

- Local audio: preserve the original and work from a safe copy or read-only reference.
- Local video: extract an audio stream into the job directory if the selected ASR tool cannot read video directly.
- Public URL: save acquired media only inside the job directory and retain public title/source metadata.
- Existing transcript: skip acquisition and ASR.

If acquisition is blocked by authentication, protection, unsupported media, or ambiguous rights, stop and ask for a local file or transcript.

#### Preserve the raw baseline

For audio or video, run:

```text
python scripts/transcribe.py INPUT --output-dir JOB_DIRECTORY
```

The script creates `raw-transcript.txt` and `segments.json` without overwriting existing files. Segment metadata is not proof of speaker identity; do not claim diarization that the tool did not perform.

Save the untouched result as `raw-transcript.txt`. It is the completeness baseline. Do not clean it in place.

### 4. Verify entities and split

#### Build entity hints

Before proofreading, verify as many of these as the public evidence supports:

- show or series title;
- episode title;
- host name and role;
- guest name and role;
- organizations, products, places, papers, and specialist terms that recur.

Prefer the official episode page, official feed metadata, the speakers' official profiles, or another first-party source. Use secondary sources only when first-party evidence is unavailable, and label the uncertainty.

Write `entity-hints.md` without private machine or account metadata. A useful entry contains:

```markdown
| Heard or raw form | Verified form | Role or meaning | Evidence status |
|---|---|---|---|
| speaker 1 | Host | host | unresolved name |
| term from ASR | Canonical Term | technical concept | verified |
```

Never convert an unresolved sound-alike into a confident name.

#### Split into bounded chunks

Split long text before proofreading:

```text
python scripts/split_transcript.py raw-transcript.txt --output-dir chunks --limit 4500 --json
```

If `chunks/` is nonempty, stop and ask whether the user wants to keep it or explicitly rebuild with `--replace`. Never remove it manually.

The splitter will:

- target at most 4,500 characters per chunk;
- prefer speaker or paragraph boundaries;
- keep stable, zero-padded ordering such as `chunk-000`, `chunk-001`, `chunk-002`;
- preserve the first and last sentence of every raw chunk for boundary checks;
- do not drop short interjections that carry agreement, disagreement, timing, or tone.

Read the chunk list plus the beginning and end of the transcript before assigning work.

### 5. Proofread and integrate

Proofread every chunk under the quality rules below. This is transcript correction, not rewriting.

When the runtime and user authorization allow parallel workers, independent chunks may be proofread in parallel. Each worker must:

- read `entity-hints.md` and the quality rules first;
- write only its assigned proofread chunk;
- preserve all meaningful speech;
- avoid modifying job state, integrated output, or another worker's chunk.

When delegation is unavailable or not authorized, process chunks serially.

A single coordinator owns:

- the executive summary;
- the first chunk;
- final speaker-name consistency;
- natural-order integration;
- boundary de-duplication;
- validation and rendering.

Integrate only non-empty, reviewed chunk files. Merge by chunk number, never by completion time.

### 6. Validate and render

Build `transcript.md` first. Validate it against `raw-transcript.txt`, then render the same content to `transcript.html`.

The HTML must be standalone and readable without network access:

- semantic headings and paragraphs;
- embedded CSS only;
- no external fonts, scripts, trackers, images, or stylesheets;
- preserved speaker emphasis and bilingual ordering;
- responsive line lengths and contrast suitable for long reading.

If HTML rendering fails, keep the valid Markdown draft, report the exact rendering limitation, and do not claim both outputs are complete.

## Quality rules

Apply this priority order whenever two editing goals conflict.

### P0 — Meaning completeness

Every meaningful claim, example, qualification, disagreement, and narrative beat in the raw transcript must remain in the verbatim transcript. Punctuation and paragraphing may increase length. Translation may increase it further. Do not compress the transcript to make it elegant.

### P1 — Entity accuracy

Use verified spellings from `entity-hints.md`. Preserve uncommon spellings and diacritics. If a person or term cannot be verified, keep a neutral label or the least-assumptive raw form and list it under `Unresolved Items`.

### P2 — Semantic-spine bolding

For a substantive passage of roughly 100 words or 200 Chinese characters or more, bold one to three complete pivotal statements when doing so helps scanning.

Bold:

- the host's sharpest question or synthesis;
- the guest's thesis;
- a counter-intuitive insight;
- decisive evidence or a key limitation.

Do not bold isolated buzzwords. A reader should be able to follow the main reasoning by reading the bold sentences, while the unbolded text still preserves the full conversation.

### P3 — Speaker and paragraph formatting

Use verified names when available:

```markdown
**Speaker Name**: English speech.

**说话人**：中文发言。
```

Keep the colon outside the bold marker. Use neutral labels such as `Speaker A` or `说话人 A` when identity remains unresolved. Break a very long turn at natural logical transitions; do not invent a speaker change.

### P4 — Spoken-text fidelity

Keep useful hesitation, humor, emphasis, and conversational texture. Remove only clear ASR noise, accidental repetitions with no meaning, and non-speech artifacts. Correct grammar only when the raw form is an ASR error or blocks comprehension. Do not turn vivid speech into formal prose.

## Language modes

### Chinese source

- Correct Chinese punctuation and ASR errors.
- Use full-width Chinese speaker punctuation: `**说话人**：`.
- Keep established English technical terms in context.
- Separate speakers and logical paragraphs with blank lines.

### English source

For English-only output, preserve the corrected English with `**Speaker Name**:` labels.

For English-to-Chinese bilingual output, keep every speech unit aligned:

```markdown
**Speaker Name**: Corrected English speech.

对应的中文翻译。
```

Do not summarize the English into a shorter Chinese paragraph.

### Mixed-language source

Use the conversation's dominant language for punctuation and paragraphing. Preserve inline names and technical terms in their spoken language. A common translation may be added at first mention when it improves comprehension; do not repeat it mechanically.

## Executive Summary

Unless the user opts out, write a concise summary before the transcript:

- focus on the central question, main positions, tension, and conclusion;
- distinguish the speakers' views from the editor's wording;
- use one or two short quotations only when they are present in the transcript;
- never treat the summary as evidence that the full transcript may be shortened.

## Output contract

Write the Markdown in this order:

```markdown
# Episode title

## Executive Summary

## Source Notes

## Verbatim Transcript

**Host**: Transcript begins here.

**Guest**: The complete conversation continues here.

## Unresolved Items
```

`Source Notes` may include public source title, public URL, spoken language, requested output mode, and material limitations. Do not include a machine path, credential, hidden prompt, internal work log, or private destination.

Omit `Unresolved Items` when there are no unresolved names, labels, inaudible passages, or unsupported claims.

The HTML must contain the same reader-facing content in the same order. Rendering may change presentation, not meaning.

## Validation

Run every applicable gate before completion.

### Artifact checks

- `transcript.md` exists, is non-empty, and contains the expected headings.
- `transcript.html` exists, is non-empty, and opens as an HTML document.
- The HTML contains the same episode title, summary, source notes, transcript, and unresolved items as the Markdown.
- Both outputs are inside the job directory or a destination explicitly selected by the user.

### Completeness checks

- Every planned chunk has one reviewed proofread chunk.
- Integrated chunks appear in numeric order.
- The final transcript begins and ends with the same meaningful content as the raw baseline.
- Adjacent chunk boundaries contain no duplicated or missing passage.
- The final transcript body is normally at least 95% of the raw baseline's character count.
- Same-language output is normally no more than 250% of the raw baseline; bilingual output may reach 350%.
- A ratio outside these bounds is a review signal, not permission to trim content mechanically.

### Quality checks

- Speaker labels use one consistent format.
- Verified names match `entity-hints.md`.
- Neutral labels remain neutral; no guessed identity appears.
- Substantive long passages use semantic-spine bolding where it improves scanning.
- Bilingual speech units remain aligned.
- No ASR-engine notes, temporary filenames, worker instructions, or debugging text appear in the reader-facing transcript.

### Privacy and HTML checks

- No username, email address, credential, machine path, temporary directory, hidden prompt, or private destination appears in either output.
- HTML uses no external runtime resource or tracker.
- Headings, links, line wrapping, and contrast remain readable at desktop and mobile widths.

## Failure handling

### Local transcription cannot be prepared

Report the exact failed check. The bundled setup may prepare its own Python runtime and model only after approval; it does not install FFmpeg, CUDA, a package manager, or another system dependency. Ask for the missing system dependency to be installed, or accept a rough transcript instead.

### A media URL cannot be acquired

Report whether the cause is unsupported media, authentication, protection, missing capability, or another observable limitation. Ask for a lawful local file or transcript. Do not bypass the restriction.

### A speaker or entity cannot be verified

Use a neutral label or conservative raw spelling. Add an `Unresolved Items` entry with the affected passage or term. Do not guess.

### A chunk fails

Keep the raw transcript and successful proofread chunks. Mark the failed chunk incomplete in `job-state.md`, correct or retry only that chunk, and do not emit the integrated draft as final.

### Validation fails

Preserve the draft, name the failed gate, correct the underlying issue, and rerun every affected check. Do not weaken the gate to obtain a pass.

### HTML rendering fails

Keep the validated Markdown. Report that HTML is incomplete and the exact observable failure. The job is not complete until the requested HTML exists and passes its checks.

## Completion gate

Do not say the job is complete until fresh evidence supports every checked item:

```markdown
- [ ] Original source preserved
- [ ] Raw transcript preserved
- [ ] Public entities checked or uncertainties labeled
- [ ] Every chunk proofread and reviewed
- [ ] Chunks integrated in numeric order
- [ ] Boundaries checked for loss and duplication
- [ ] Transcript size compared with the raw baseline
- [ ] Speaker and language formatting validated
- [ ] Markdown exists and is non-empty
- [ ] Standalone HTML exists and is non-empty
- [ ] Markdown and HTML contain the same reader-facing content
- [ ] Privacy and machine-path scan passed
- [ ] No external HTML runtime request is required
- [ ] Nothing was uploaded or published
```

Report the two local deliverables and any unresolved items. Then stop.
