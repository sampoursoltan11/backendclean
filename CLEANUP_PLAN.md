# Phase 1: Code Cleanup Plan

## Overview
Removing ~650 lines of unused code from the TRA backend system.

## Changes to Make

### 1. Clean Up Models File (tra_models.py)
**File**: `code/models/tra_models.py`
**Lines to Remove**: ~540 lines (Lines 349-923)

#### Unused Models (Never Instantiated):
- `RiskAreaSegment` (Lines 349-383) - 35 lines
- `EnhancedTRAAssessment` (Lines 385-503) - 119 lines
- `AgentDecisionType` enum (Lines 546-559) - 14 lines
- `AgentPerformanceMetric` enum (Lines 561-571) - 11 lines
- `ConversationPhase` enum (Lines 573-582) - 10 lines
- `AgentDecision` (Lines 584-619) - 36 lines
- `ConversationContext` (Lines 621-660) - 40 lines
- `AgentPerformanceMetrics` (Lines 662-693) - 32 lines
- `RAGRetrievalRecord` (Lines 709-749) - 41 lines
- `DecisionTreeAnalytics` (Lines 751-785) - 35 lines
- `AgentLearningRecord` (Lines 787-815) - 29 lines
- Response Models (Lines 819-923) - 105 lines total:
  - `AgentPerformanceResponse`
  - `ConversationInsightsResponse`
  - `RAGPerformanceResponse`
  - `DecisionAnalyticsResponse`
  - `LearningInsightsResponse`
  - `RiskAreaOverviewResponse`
  - `EnhancedTRAResponse`
  - `TRACompletionMatrixResponse`
  - `TRARecommendationsResponse`

**Models to KEEP** (Actually Used):
- `AssessmentState` - Used in status_tools.py, assessment_tools.py
- `EventType` - Used in status_tools.py
- `TraAssessment` - Core model, used everywhere
- `TraEvent` - Used in status_tools.py
- `DocumentMetadata` - Used in file_tracking_service.py
- `UserRole`, `RiskAreaStatus`, `TRAComplexity` - Enums defined but needed for schema
- `AssessmentReview`, `ExportRecord`, `UserProfile` - Schema models
- `ChatMessage` - Chat functionality
- `AssessmentResponse`, `StatusResponse`, `ChatResponse`, `HealthCheckResponse` - API responses
- `TRASharedState` - Used for compatibility (Lines 698-707)

### 2. Remove Unused Config Files
**Files to Delete**:
- `code/config/decision_tree1.yaml` - Old version, not used
- **Keep**: `decision_tree2.yaml` - Currently used (config points to decision_tree3.yaml but code handles both formats)

**Action**: Check which file is actually being used, delete the other

### 3. Clean Up DynamoDB Service (dynamodb_service.py)
**File**: `code/services/dynamodb_service.py`

#### Methods to Review (Potentially Unused):
- `put_item()` (Lines 505-528) - Generic method, check usage
- `get_item()` (Lines 530-541) - Generic method, check usage
- `query_gsi()` (Lines 543-608) - Complex query method, check usage
- `batch_write()` (Lines 610-625) - Batch operations, check usage
- `update_item()` (Lines 627-654) - Generic update, check usage

**Note**: These methods appear to be for "Enhanced Schema Support" but may not be actively used. Need to verify with grep.

### 4. Remove In-Memory Fallback Code
**File**: `code/services/dynamodb_service.py`

The service has in-memory fallback logic that's never used (Line 26: `_use_aws = True` is forced):
- Lines 101-103, 230-234, 243-249, 259-260, 269-271, 280-281, 300-302, etc.
- All `if not self._use_aws:` blocks can be removed since AWS is always used

**Estimated Cleanup**: ~50 lines

### 5. Clean Up Config File
**File**: `code/core/config.py`
**Line 55**: `decision_tree_config_path: str = "backend/config/decision_tree3.yaml"`

**Action**:
- Verify which config file is actually used
- Update path to correct file
- Delete unused config file

## Summary of Deletions

| File | Lines Removed | Description |
|------|--------------|-------------|
| `tra_models.py` | ~540 | Unused analytics/performance models |
| `decision_tree1.yaml` | ~49KB | Old decision tree config |
| `dynamodb_service.py` | ~50-100 | In-memory fallback code |
| **Total** | **~650 lines** | **Plus 1 large config file** |

## Models Usage Verification

### Used Models (Found in codebase):
```python
from backend.models.tra_models import DocumentMetadata     # file_tracking_service.py:17
from backend.models.tra_models import AssessmentState      # status_tools.py:138
from backend.models.tra_models import TraEvent, EventType  # status_tools.py:637
from backend.models.tra_models import TraAssessment, AssessmentState  # assessment_tools.py:94
```

### Unused Models (No imports found):
- EnhancedTRAAssessment
- RiskAreaSegment
- AgentDecision
- ConversationContext
- AgentPerformanceMetrics
- RAGRetrievalRecord
- DecisionTreeAnalytics
- AgentLearningRecord
- All analytics response models

## Risks & Considerations

1. **TRASharedState** (Lines 698-707) - Keep this! Used for variant compatibility
2. **ConversationPhase** - Used by TRASharedState, keep enum
3. **Base enums** (UserRole, RiskAreaStatus, etc.) - Keep, they're schema definitions
4. **Response models** at lines 506-542 - Keep, they're API contracts

## Execution Steps

1. ✅ Create this cleanup plan
2. ⏳ Verify which decision_tree file is used
3. ⏳ Delete unused config file
4. ⏳ Remove unused models from tra_models.py (540 lines)
5. ⏳ Remove in-memory fallback code from dynamodb_service.py (~50 lines)
6. ⏳ Remove unused generic DynamoDB methods (if verified unused)
7. ⏳ Test that nothing breaks
8. ✅ Commit changes

## Post-Cleanup Benefits

- **Smaller codebase**: ~650 lines removed (6.5% reduction)
- **Faster load times**: Less Python import overhead
- **Better maintainability**: Less code to understand
- **Clearer intent**: Only production code remains
- **Easier testing**: Fewer models to mock/test
