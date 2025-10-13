# 2PC Trade Mechanism - State Transition Diagram

## State Transition Diagram

```
                          [START]
                             |
                             | trade create
                             v
                    +------------------+
                    |                  |
                    |     PENDING      |<----+
                    |                  |     |
                    +------------------+     |
                       /           \         |
                      /             \        |
           accept    /               \ reject/cancel
                    /                 \      |
                   v                   v     |
         +-----------------+      +----------+-------+
         |                 |      |                  |
         |    ACCEPTED     |      |     REJECTED     |
         |                 |      |    / CANCELED    |
         +-----------------+      +------------------+
                  |                        |
    confirm (both)|                        |
      parties     |                        v
                  v                    [END - Failed]
         +-----------------+
         |                 |
         |   CONFIRMED     |
         | (both parties)  |
         +-----------------+
                  |
       execute    |
       (atomic)   |
                  v
         +-----------------+
         |                 |
         |    COMPLETED    |
         |                 |
         +-----------------+
                  |
                  v
              [END - Success]
```

## Detailed State Description

### 1. **PENDING** (Initial State)
- **Entry**: Trade request created by initiator
- **Description**: Waiting for target to accept or reject
- **Available Actions**:
  - Target: `accept` → ACCEPTED
  - Target: `reject` → REJECTED
  - Initiator: `cancel` → CANCELED
- **Data Stored**:
  - `initiator_id`, `target_id`
  - `offer_type` (buy/sell)
  - `item`, `quantity`, `price`
  - `initiator_confirmed: false`
  - `target_confirmed: false`

### 2. **ACCEPTED** (Preparation Phase)
- **Entry**: Target accepts the trade
- **Description**: Both parties must confirm to proceed
- **Resource Validation**: System checks if target has sufficient resources
- **Available Actions**:
  - Initiator: `confirm` → sets `initiator_confirmed = true`
  - Target: `confirm` → sets `target_confirmed = true`
  - When both confirm → CONFIRMED
- **Important**: Trade stays in this state until BOTH parties confirm

### 3. **CONFIRMED** (Ready to Execute)
- **Entry**: Both parties have confirmed (`initiator_confirmed && target_confirmed`)
- **Description**: Trade is ready for atomic execution
- **Next Step**: Automatic atomic execution
- **Transition**: Immediate → COMPLETED (if successful)

### 4. **COMPLETED** (Terminal State - Success)
- **Entry**: Trade executed successfully
- **Description**: All resources transferred atomically
- **Execution Steps** (atomic):
  1. Buyer pays money
  2. Seller deducts item
  3. Buyer receives item
  4. Seller receives money
- **Post-action**: Trade removed from active trades

### 5. **REJECTED** (Terminal State - Failure)
- **Entry**: Target rejects the trade request
- **Description**: Trade declined, no resource changes
- **Condition**: Only possible from PENDING state

### 6. **CANCELED** (Terminal State - Failure)
- **Entry**: Initiator cancels the trade request
- **Description**: Trade withdrawn, no resource changes
- **Condition**: Only possible from PENDING state

---

## State Transition Rules

| Current State | Action | Actor | Next State | Conditions |
|--------------|--------|-------|------------|------------|
| PENDING | accept | Target | ACCEPTED | Target has sufficient resources |
| PENDING | reject | Target | REJECTED | - |
| PENDING | cancel | Initiator | CANCELED | - |
| ACCEPTED | confirm | Initiator | ACCEPTED* | Sets `initiator_confirmed = true` |
| ACCEPTED | confirm | Target | ACCEPTED* | Sets `target_confirmed = true` |
| ACCEPTED | confirm (both) | Both | CONFIRMED | Both flags set to true |
| CONFIRMED | execute | System | COMPLETED | Atomic execution succeeds |

*Note: ACCEPTED state remains until both parties confirm

---

## API Endpoints and State Changes

```
POST /trade/create
  → Creates trade in PENDING state

POST /trade/accept
  → PENDING → ACCEPTED (with resource validation)

POST /trade/confirm
  → ACCEPTED → CONFIRMED (when both confirmed)
  → CONFIRMED → COMPLETED (automatic execution)

POST /trade/reject
  → PENDING → REJECTED

POST /trade/cancel
  → PENDING → CANCELED

GET /trade/list
  → Query trades by status
```

---

## Example Trade Flow

### Successful Trade: Alice buys wheat from Bob

```
1. [PENDING] Alice: trade create
   - Alice (node1) → Bob (node2): buy 3 wheat for 21 gold
   - Status: PENDING
   - initiator_confirmed: false, target_confirmed: false

2. [ACCEPTED] Bob: accept trade_1
   - System validates: Bob has 3+ wheat
   - Status: ACCEPTED
   - initiator_confirmed: false, target_confirmed: false

3. [ACCEPTED] Bob: confirm trade_1
   - Status: ACCEPTED
   - initiator_confirmed: false, target_confirmed: true

4. [CONFIRMED → COMPLETED] Alice: confirm trade_1
   - Status: CONFIRMED (both flags true)
   - System executes atomically:
     a. Alice pays 21 gold
     b. Bob loses 3 wheat
     c. Alice gains 3 wheat
     d. Bob gains 21 gold
   - Status: COMPLETED
   - Trade removed from active trades
```

### Failed Trade: Rejection

```
1. [PENDING] Alice: trade create
   - Alice → Bob: buy 5 wheat for 50 gold
   - Status: PENDING

2. [REJECTED] Bob: reject trade_1
   - Bob declines (maybe price too low)
   - Status: REJECTED
   - No resource changes
```

### Failed Trade: Cancellation

```
1. [PENDING] Alice: trade create
   - Alice → Bob: buy 3 wheat for 21 gold
   - Status: PENDING

2. [CANCELED] Alice: cancel trade_1
   - Alice withdraws offer
   - Status: CANCELED
   - No resource changes
```

---

## Atomic Execution Guarantee

The COMPLETED state ensures atomic execution with rollback capability:

```python
def execute_trade(trade):
    try:
        # 1. Buyer pays money
        if not deduct_money(buyer): 
            return False
        
        # 2. Seller deducts item
        if not remove_item(seller):
            refund_money(buyer)  # Rollback
            return False
        
        # 3. Buyer receives item
        if not add_item(buyer):
            return False
        
        # 4. Seller receives money
        if not add_money(seller):
            return False
        
        return True
    except:
        # Any failure triggers rollback
        return False
```

---

## Key Features

1. **Two-Phase Commit**: 
   - Phase 1: Accept (preparation + resource validation)
   - Phase 2: Confirm (both parties must agree)

2. **Resource Validation**: 
   - Checked during `accept` to ensure feasibility

3. **Atomic Execution**: 
   - All-or-nothing resource transfer
   - Rollback on any failure

4. **Centralized Management**: 
   - Merchant node coordinates all trades
   - Single source of truth for trade state

5. **Safety**: 
   - No partial trades
   - No resource duplication
   - Clear state transitions

