# Style guide

## Narrative voice

Write hard, dry, and warm underneath. Prefer concrete details, economical dialogue, and humour that sounds like people coping rather than performing. Let characters disagree in specific, human ways. Avoid constant grimness; kindness, teasing, and ordinary routine are part of survival.

## World and characters

- Keep the setting material and grounded: no magic, no zombies, and no miraculous resource fixes.
- Let scarcity shape choices without reducing people to their scarcity value.
- The protagonist's mutation and political importance are facts of the setting, not substitutes for personality or relationships.
- Give companions independent goals, boundaries, skills, and reasons to stay or leave.
- Write intimacy and reproduction as consensual and character-led. Political pressure is not consent.

## Presentation

Use short paragraphs and clear choices suited to a visual novel and point-and-click interface. Keep system messages, resource deltas, and time costs explicit. UI wording should be concise and consistent; use the same name for a resource or action throughout the game.

## Visual prompt policy

All image-generation prompts must stay **SFW**. Adult content is text-only for now. Visual prompts should describe clothing, pose, scene, lighting, and mood without nudity or explicit sexual content. This rule applies to character art, backgrounds, gallery images, and promotional assets.

## STYLE_LOCK

Use this prompt string verbatim as the prefix of every later image prompt:

```text
Full body character sprite, single figure, adult male, 2.05m, heavy build, wasteland survivor, chitin-plated left forearm and shoulder, glowing amber eyes, shaved head with stubble, jaw scar, tire-rubber and sheet-steel armor over a knee-length canvas coat, fingerless gloves, heavy boots. Anime visual novel cel-shaded style, thick clean lineart, two-tone shadow. Three-quarter front view, neutral A-pose, arms clear of body, flat expression. Solid flat magenta background. Four small black L-shaped registration marks, one per corner, inset 24px, clear of the figure. No text, no border, fully clothed.
```

- Seed: `4410`
- Canvas: `768x1280`
- Registration-mark tick inset: `24px`

For every subsequent image, prefix the prompt with the exact STYLE_LOCK text above, and use the same seed (`4410`) and canvas (`768x1280`). Do not edit, paraphrase, or omit any part of the lock.
