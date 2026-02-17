# WhatsApp API Basic Chat Guide

This document provides a minimal guide for basic WhatsApp chat functionality: sending and receiving messages, including photos and documents.

## Basic Features

- Send and receive text messages between users and the system.
- Support for sending and receiving photos and documents.

## Implementation Notes

- Use Django views and models to handle chat messages.
- Use the WhatsApp Business API or a library to send/receive messages.
- For media (photos, documents), handle file uploads and downloads in your Django views and templates.

## Example Steps

1. Set up webhook to receive incoming messages (text, photo, document).
2. Implement a view to send messages (text, photo, document) to users.
3. Store messages and media in your database and media folder.
4. Display chat history in your dashboard or chat template.

## Next Steps

- Add safety features (opt-in, rate limiting, content validation, etc.) as needed, one by one.

---

This file will be updated as you add more features.
