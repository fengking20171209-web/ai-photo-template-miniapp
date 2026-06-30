# Phase 3 Boundary Design: Asset Waterfall Plan

This document outlines the strict boundaries and goals for Phase 3. The main focus is implementing core asset management UI (waterfall pagination) and fundamental database storage logic without drifting into over-engineered solutions.

## Phase 3 Scope (Allowed)

1. **Asset Persistence (落库)**
   - Storing image asset metadata (URLs, relationships to prompts/tasks) in the database via basic CRUD operations.
   - Managing asset lifecycle state (active, deleted).

2. **Waterfall Pagination (瀑布流分页)**
   - Implementing cursor-based or offset-based pagination at the API level for scalable UI rendering.
   - Building a masonry/waterfall frontend layout to gracefully display assets.

3. **Basic Favorites/Collection (基础收藏)**
   - Allowing users to mark generated assets as favorites.
   - Storing "favorited" state in the database using a simple relation table or column.

## Phase 3 Out-of-Scope (Not Allowed)

1. **Cloud Storage SDK Integrations (云存储SDK)**
   - Direct integration with AWS S3, Tencent COS, or Aliyun OSS SDKs for upload processes during this phase. (Assume URLs are handled/provided externally or simulated).

2. **Distributed Queues (分布式队列)**
   - Setting up Celery, Redis Queue, or RabbitMQ for asynchronous task processing.
   - Stick to lightweight, synchronous or simple background task processing if necessary.

3. **Image Moderation/Review (图片审核)**
   - Integrating third-party APIs for NSFW/content moderation of images.
   - Complex moderation workflows and review statuses.

## Design Philosophy
Keep the architecture light. We are freezing the current Phase 2A database foundation and API contracts. Phase 3 focuses entirely on user-facing asset presentation and reliable (but simple) state management.
