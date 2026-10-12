# Round protocol

The operating rules for this work come from the Sol 6.1 base instructions, imported verbatim to
`docs/porting/sol-agent-prompt.md`. What follows is only the part that changes a porting round.

## One round

- Lead the turn with the measured result and its number. One measurement, one `## §NN` section, one
  commit. Numbers appear once, inside a fenced block; later mentions cite the section (`§317`).
- Batch independent shell reads into a single call and keep a round to 5-10 tool calls.
- Treat the standing objective as authorization: act inside the round, ask only when the answer changes
  what gets measured.
- Do not settle for a partial result to save effort; report a thin result as thin, name the criterion
  that would settle it, and say which instrument carries it.
- Name the failure mode a criterion could hit before trusting a match. A relation needs a nonzero reading
  and several distinct operands behind it; a row needs witnesses.
- Close with: the measurement in a fence, three keeper lines, the evidence sha, the commit, the
  porcelain count, and the goal line. No closing summary.

## Imported style rules that apply here

Plain language, active voice, point first. Each sentence builds on the one before. Headings carry the
result, not a narration of the round. No "what this is not" filler, no inventory of unchanged parts, no
"in short" recap. Technical detail enters only where it changes the conclusion.
