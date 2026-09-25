# Page brief: Notification preferences

## Purpose

Let team admins choose which events send them email, so they stop getting alerts they ignore and trust the ones they get. It should feel clean and modern.

## Users and context

- **Who:** team admins, a few times a month, usually right after getting an email they didn't want
- **Device:** mostly phone. Most arrive from the "Manage notifications" link at the bottom of an email.
- **Arrives from:** the email link, or Settings → Notifications

## Goals (ranked)

1. Admins can turn off the emails they don't want without contacting support
2. Admins can check a change worked by sending themselves a test email

## What users need to do

- Turn off email for one type of event — starts from: the email link
- Change how often digests are sent, with a dropdown — starts from: Settings → Notifications
- Send a test email

## Content and data

- A list of event types, grouped by area (billing, security, reports, etc.)
- Each event type has an on/off setting for email; digests have a frequency

## States

- **Loading:** settings load from the server; can take a second on mobile
- **Empty:** new teams have the default settings, so it's never empty
- **Success:** a confirmation after saving

## Constraints

- Security emails can't be turned off (legal requirement), but must still show on the page
- Ship before the Q4 billing change

## Acceptance criteria

- An admin can turn off email for one event type from the email link
- The page is easy to use
- The Save button should pop, and "Send test email" should be just as visible

## Out of scope

- Push and SMS notifications (a later project)

## Related pages and designs

- Settings pages generally

## Open questions

- Should changes save instantly, or with a Save button?
