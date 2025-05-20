# Architectural Decision Record: Real-time Progress Reporting Protocol

## Status

Accepted

## Context

The RFM-Architecture application performs intensive computational operations when rendering fractals and animations. These operations can take significant time, especially for complex fractals, high resolutions, or many iterations. The current implementation provides limited feedback during these operations, resulting in a poor user experience due to:

1. Users have no visibility into progress during long-running operations
2. The UI can appear frozen during intensive calculations
3. There's no ability to cancel in-progress operations
4. Operations that fail part-way through don't provide partial results

The application has an existing asynchronous rendering system using an async queue, but it lacks interim progress reporting. We need a bi-directional real-time communication protocol between the backend computation modules and the frontend UI to address these limitations.

## Decision

We will implement a WebSocket-based real-time progress reporting protocol with the following characteristics:

1. **Protocol**: WebSocket (over asyncio)
   - Reason: WebSockets provide full-duplex communication, allowing real-time updates from both client and server. This is more appropriate than Server-Sent Events (SSE) as we require bidirectional communication for operation cancellation.

2. **Server Implementation**:
   - Leverage Python's asyncio and websockets libraries
   - Implement a progress manager to track and broadcast operation status
   - Support multiple concurrent operations with unique IDs

3. **Client Implementation**:
   - Integrate WebSocket client in the UI layer
   - Add progress visualization components (progress bars, percentage completion)
   - Implement operation cancellation UI

4. **Message Structure**: Use JSON for message encoding with the following types:
   - `progress_update`: Report progress percentage and status
   - `operation_started`: Signal the start of a tracked operation
   - `operation_completed`: Signal operation completion
   - `operation_failed`: Report operation failure with error details
   - `operation_canceled`: Acknowledge cancellation
   - `cancel_request`: Request to cancel an operation

5. **Protocol Flow**:
   - Backend initiates progress tracking with unique operation ID
   - Regular progress updates sent during computation
   - Frontend displays progress and allows cancellation
   - Cancellation requests propagated to computation code
   - Final status update with complete results or error information

## Message Format

```json
{
  "type": "progress_update",
  "operation_id": "unique-id-1234",
  "timestamp": 1620000000.123,
  "data": {
    "progress": 45.5,
    "status": "computing",
    "current_step": "Computing fractal iterations",
    "total_steps": 100,
    "current_step_progress": 45.5,
    "estimated_time_remaining_ms": 5000,
    "memory_usage_mb": 256.5
  }
}
```

## Operation Type Examples

1. **Fractal Rendering Progress**:
   - Track percentage of pixels processed
   - Report iteration depth statistics
   - Provide preview of in-progress render

2. **Animation Generation**:
   - Track frames rendered vs total frames
   - Report time per frame
   - Allow frame-by-frame preview

3. **L-System Generation**:
   - Track recursion depth progress
   - Report number of segments generated

## Consequences

### Positive

- Users gain visibility into long-running operations
- The application feels more responsive with real-time feedback
- Users can cancel operations they no longer want to wait for
- Partial results can be displayed for improved user experience
- Operations that encounter issues can provide detailed error information

### Negative

- Increased architectural complexity
- Additional performance overhead for progress tracking
- Potential memory usage increase due to storing intermediate results
- Need to ensure WebSocket reconnection logic for robustness

## Implementation Plan

1. Create new modules for WebSocket server and client
2. Modify core computation code to report progress
3. Add Progress Manager to track multiple operations
4. Implement UI components for progress visualization
5. Add cancellation support in computation code
6. Enhance error handling for partial failures

## Dependencies

- Python websockets library for backend
- WebSocket handling in frontend (DearPyGui integration)
- Updates to core computation modules to report progress

## Resources

- [Python websockets library](https://websockets.readthedocs.io/)
- [DearPyGui documentation](https://dearpygui.readthedocs.io/)
- [Asyncio documentation](https://docs.python.org/3/library/asyncio.html)