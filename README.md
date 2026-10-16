# podcast-trancript-public

Turn podcast audio, video, episode links, or rough transcripts into clean, readable transcripts.

The skill fixes punctuation and paragraph breaks, checks names and speaker labels, and keeps the substance of the conversation intact. It produces Markdown for editing and HTML for reading or sharing.

[View the installable skill](./podcast-trancript-public/SKILL.md) · [English introduction](./docs/index.html) · [中文介绍](./docs/zh.html)

## What it works well with

- Podcast interviews and roundtables
- Long-form video or recorded conversations
- Rough transcripts with poor punctuation or frequent recognition errors
- English, Chinese, or bilingual material

## Install

Call `$skill-installer` in Codex and give it the skill's GitHub address:

```text
Use $skill-installer to install this skill: https://github.com/ZHUCH-520/podcast-trancript-public/tree/main/podcast-trancript-public
```

Once installed, send an episode link:

```text
Use $podcast-trancript-public to process this podcast in English and create Markdown and HTML: <episode link>
```

You can also choose local audio or video:

```text
Use $podcast-trancript-public to edit this recording in English and create Markdown and HTML.
```

If you already have a rough transcript, send the text directly. Speech recognition is not required.

## Your first audio or video

You do not need to set up Whisper in advance. When the skill receives audio or video for the first time, it checks your computer and shows a setup plan before downloading anything:

- Whether your computer will use MLX Whisper or faster-whisper
- Which model it recommends, with the option to choose another
- The approximate download size and storage location
- What requires a network connection

| Model | Best for | Tradeoff |
|---|---|---|
| `small` | Trying one episode or using modest hardware | Small and fast; names, accents, and noisy audio may need more correction |
| `turbo` | A newer Apple Silicon Mac, or Windows or Linux with a suitable GPU | A good balance of speed and accuracy |
| `large-v3` | Name-heavy shows, strong accents, or uneven recordings | The largest download, with higher memory and processing needs |

Apple Silicon Mac uses MLX Whisper. Intel Mac, Windows, and Linux use faster-whisper. On Windows and Linux, CUDA with float16 is used when it is available; otherwise faster-whisper runs on CPU with int8. Models are stored in your operating system's user cache, not inside the skill folder.

Already have a rough transcript? Skip Whisper and the model download—the skill goes straight to checking and editing the text.

## What you get

- `transcript.md`: a transcript that is easy to edit or move into a notes app
- `transcript.html`: a readable page you can open directly
- `Unresolved Items`: included only when a name, term, or speaker still needs checking

The basic transcript structure is:

```markdown
# Episode title

## Summary

## Source notes

## Full transcript

## Unresolved items
```

The summary is an entry point. It never replaces the full transcript.

## How it works

1. Identify whether the source is a link, audio, video, or existing text, then confirm the output language.
2. Create a folder for the episode and preserve the original media and rough transcript.
3. Check the local transcription setup and show the model, download size, and storage location. Preparation starts only after approval.
4. Verify guest names and terminology against the episode page, then split long transcripts losslessly with the bundled script.
5. Fix punctuation, speaker labels, and obvious recognition errors one chunk at a time.
6. Merge the chunks, check the beginning, ending, gaps, duplicates, and formatting, then create Markdown and HTML.

Claims, examples, caveats, and useful speaking habits stay in the transcript. If a speaker's identity cannot be confirmed, the skill uses a neutral label such as `Speaker A` instead of guessing.

Optional local diarization can add IDs such as `SPEAKER_00`. It stays off until you approve a separate download. Those IDs are not names; the skill still checks them against the episode page.

## Where files go

After local transcription is ready, the audio and models remain on your computer. Models live in the system user cache; episode files and transcripts stay in the folder created for that task.

The skill explains when it needs the network to fetch an episode or verify public information. Sending audio to a cloud transcription service requires your explicit approval.

Generated transcripts do not include usernames, email addresses, local computer paths, credentials, or internal logs. The introduction pages have no analytics scripts, tracking pixels, or remote fonts.

## What it does not do

- Bypass paywalls, sign-ins, DRM, or platform protections
- Guarantee automatic identification of every speaker
- Automatically install FFmpeg, CUDA, system package managers, or modify system settings
- Upload, sync, or publish generated files automatically
- Recommend shows or maintain listening history

## Troubleshooting

| Situation | What to do |
|---|---|
| First time processing audio or video | Review the setup plan, then choose `small`, `turbo`, or `large-v3` |
| FFmpeg, CUDA, or another system dependency is missing | Install the dependency shown in the report; the setup script does not modify system settings for you |
| An episode link cannot be read | Provide audio, video, or text that you obtained legally |
| A speaker cannot be identified | Share the official episode page or correct name, or keep a neutral label |
| One chunk fails | Keep the completed chunks and retry only the failed one after fixing the cause |
| HTML is not generated | Keep the checked Markdown, then regenerate the HTML version |

## Repository contents

- [`SKILL.md`](./podcast-trancript-public/SKILL.md): the skill's instructions
- `README.md`: installation and usage guidance
- [`index.html`](./docs/index.html): the English GitHub Pages introduction
- [`zh.html`](./docs/zh.html): the Chinese GitHub Pages introduction

## License

MIT License. Copyright (c) 2026 ZHUCH-520.
