# Page brief: Hackathon voting

## Purpose

Let attendees vote for their favourite games at the end of the hackathon, so winners are picked fairly and quickly.

## Users and context

- **Who:** attendees and participants, once per hackathon, all at the same time at the closing session
- **Device:** almost always a phone, at the event

## Where it fits

- **Arrives from:** a QR code shown on screen at the closing session, or the event link
- **Goes next:** a thank-you, then the results when they're announced
- **Pages that should link here:** the hackathon page

## Goals (ranked)

1. Every attendee can vote for their favourite games in under a minute
2. Organizers can trust the result: one person, three votes

## What users need to do

- Browse the games and vote for my favourites — starts from: the QR code
- Change my votes before voting closes — starts from: the voting page

## What this page depends on

- **Games:** shown as cards with a title, team and thumbnail · comes from: unknown
- **Votes:** created by attendees on this page · comes from: this page

## Content and data

- About 40 games per hackathon, each with a title, team name and thumbnail
- Each attendee has 3 votes

## States

- **Loading:** the game list loads when the page opens
- **Empty:** voting isn't open yet
- **Error:** a vote fails to save
- **Success:** the vote is confirmed

## Constraints

- Ship before the spring hackathon

## Acceptance criteria

- An attendee can cast 3 votes in under a minute on a phone, at 320px
- A person can't cast more than 3 votes

## Out of scope

- Judges' scoring (a separate panel)

## Related pages and designs

- The hackathon page

## Open questions

- None
