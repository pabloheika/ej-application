# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [3.4.0] - Jun 29, 2024

### Added

- New checkbox field in Conversation form to disable participants from adding comments.
- SMTP module accepts configuring SMTP servers without using anymail package.
- Upgrades to Python 3.9

### Changed

- Comments API returns 403 if conversation have comment addition disabled.

## [3.3.1] - Jun 12, 2024

### Changed

- Fixes conversation time chart start_date and end_date.
- Renames user default board to "Explorar".
- When voting as a persona, the comment will stay at the same position.
- Fixes participation page overflow.
- Adds to the documentation a reference to an EJ thesis developed by an UnB student.
- Improves navigation menu interface, based on Figma prototypes.

## [3.3.0] - Jun 3, 2024

### Added

- Enables the user to visualize some cluster statistics by clicking on it in the conversation panel.
- New side navigation menu for logged user.
- Add the convergence column to the comments report.
- New side navigation menu for conversation participant.
- [api]: Adds support for JWT authentication.

### Changed

- Fix comment report statistics when selecting multiple clusters.
- Fix side navigation menu when editing a conversation.
- Shows conversation title in the side navigation menu.
- Fix bug that breaks Django when clusterizing personas without votes.
- [mobile]: Fix side navigation menu for conversation participant.

### Removed

- Revert the commit that includes comments without votes in the comments report.

## [ADA LOVELACE] - October 11, 2018

## Added

- Participate on conversations with votes and comments
- Add conversation to favorites
- Track your comments on conversations viewing how they perform with other users
- Create new conversations and organize them on boards
- Accept or reject comments with reasoning
- Define stereotypes on conversations to read reports of opinion groups
- Fill your profile information with a personalized picture
- Read basic documentation about how to use EJPlatform
