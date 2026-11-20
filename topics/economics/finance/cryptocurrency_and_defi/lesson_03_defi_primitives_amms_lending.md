# Lesson 3: DeFi Primitives—Automated Market Makers, Lending Protocols, Stablecoins

## 1. First-Principles Intuition & Invariants

The decentralized finance revolution fundamentally rewrites the institutional architecture of financial intermediation by replacing trusted human operators with verifiable algorithmic primitives deployed as immutable smart contracts on public blockchains. Traditional finance relies on centralized orderbook exchanges, fractional reserve banks, and fiat-backed stablecoins managed by corporations subject to regulatory oversight and operational risk. DeFi inverts this model by constructing financial primitives as transparent, non-custodial protocols where execution logic is encoded in Solidity or Vyper, settled atomically on Ethereum Virtual Machine compatible chains, and secured by cryptographic consensus rather than legal contracts.

The three foundational DeFi primitives—automated market makers (AMMs), collateralized lending protocols, and algorithmic stablecoins—form a compositional stack that enables permissionless liquidity provision, programmable credit markets, and synthetic price stability without centralized intermediaries. Each primitive solves a specific coordination problem in distributed financial systems. AMMs resolve the liquidity bootstrapping problem inherent in orderbook exchanges by enabling passive market making through bonding curve formulas. Lending protocols construct on-chain money markets where interest rates emerge from algorithmically governed supply-demand equilibria rather than centralized rate-setting committees. Stablecoins provide price-stable reference assets pegged to external numeraires, enabling economic calculation and hedging within an otherwise volatile cryptoasset ecosystem.

Understanding these primitives requires dissecting their game-theoretic incentive mechanisms, their capital efficiency tradeoffs, and their systemic failure modes under adversarial conditions. The constant product formula $x \cdot y = k$ governing Uniswap-style AMMs encodes a specific liquidity provision strategy with predictable slippage characteristics and impermanent loss exposure. Compound Finance's utilization-based interest rate model $r_t = r_0 + \frac{u_t}{1-u_t} \cdot r_{\text{slope}}$ dynamically adjusts borrowing costs to maintain protocol solvency. Algorithmic stablecoins like Terra's UST implement reflexive peg maintenance mechanisms where arbitrage between the stablecoin and a volatile collateral asset theoretically maintains price stability—until reflexivity inverts during bank runs.

The critical invariant across all DeFi primitives is atomicity through smart contract execution. Unlike traditional financial systems where settlement involves multi-party clearing, netting, and reconciliation across days, DeFi transactions execute atomically within single blockchain blocks. This property enables flash loans—uncollateralized loans that must be repaid within the same transaction—and complex multi-protocol arbitrage strategies that exploit momentary price dislocations across decentralized exchanges, lending markets, and derivative protocols. The composability of DeFi primitives creates a dense dependency graph where protocol risk compounds systemically, as demonstrated during the May 2021 liquidation cascade triggered by a 50% Ether price drop that propagated through overleveraged positions in Aave, Compound, and MakerDAO simultaneously.

## 2. Core Architecture & Mechanics

### Automated Market Makers and the Constant Product Invariant

The Uniswap V2 constant product AMM implements a remarkably simple yet powerful market-making algorithm. Each liquidity pool maintains reserves of two tokens, denoted $x$ and $y$, constrained by the invariant $x \cdot y = k$ where $k$ represents the pool's constant product. When a trader swaps $\Delta x$ units of token X for some amount $\Delta y$ of token Y, the protocol calculates the output quantity by solving $(x + \Delta x)(y - \Delta y) = k$ to preserve the invariant. After accounting for the 0.3% fee that accrues to liquidity providers, the swap execution formula becomes:

$$\Delta y = \frac{y \cdot \Delta x \cdot 0.997}{x + \Delta x \cdot 0.997}$$

This bonding curve creates a hyperbolic price relationship where the marginal exchange rate $\frac{dy}{dx} = -\frac{y}{x}$ equals the negative ratio of reserves. As traders drain one side of the pool, the price moves adversely along the curve, creating slippage that grows quadratically with trade size. A trader swapping 10% of the pool's X reserves faces approximately 5% price impact, while a 50% swap incurs over 33% slippage. This automated market making mechanism differs fundamentally from orderbook exchanges where liquidity providers post discrete limit orders at specific price levels. The AMM continuously quotes prices across the entire curve, providing infinite liquidity up to the reserve depletion point, but at the cost of predictable slippage.

Liquidity providers deposit paired reserves into pools, receiving fungible LP tokens representing their proportional ownership. The provider earns trading fees proportional to their pool share but faces impermanent loss—a position-marking effect where the AMM rebalancing mechanism systematically underperforms a passive hold strategy during directional price moves. Consider a liquidity provider who deposits equal-value amounts of ETH and USDC when ETH trades at $2000. If ETH doubles to $4000, the constant product formula forces the pool to rebalance such that the provider's position contains fewer ETH and more USDC than their initial deposit. The impermanent loss formula quantifies this effect:

$$IL = \frac{2\sqrt{r}}{1+r} - 1$$

where $r$ represents the price ratio change. A 2x price move generates 5.7% impermanent loss, while a 5x move produces 25.5% loss relative to holding. This loss becomes permanent only when the provider withdraws liquidity; if prices revert to the original ratio, the loss disappears. However, the opportunity cost remains real because the provider's rebalanced position captures less upside during bull markets. Fee income must exceed impermanent loss for liquidity provision to remain profitable, creating a volatility-to-volume ratio threshold below which passive LPs earn positive returns.

Uniswap V3 introduced concentrated liquidity, allowing providers to allocate capital within specific price ranges rather than across the entire 0-to-infinity curve. A provider can concentrate liquidity in the $1900-$2100 range for an ETH/USDC pool, earning proportionally higher fees when prices trade within that band while earning nothing outside it. This capital efficiency improvement comes at the cost of active management requirements and higher impermanent loss exposure within the concentrated range. The effective liquidity provided by a V3 position equals:

$$L = \frac{\Delta y}{\sqrt{P_b} - \sqrt{P_a}}$$

where $P_a$ and $P_b$ bound the price range. A tightly concentrated position provides 10-100x the effective liquidity of a V2 full-range position with the same capital, but experiences proportionally amplified rebalancing effects.

```text
Uniswap V2 Pool State Transition:

Initial State:
  Reserve X: 100 ETH
  Reserve Y: 200,000 USDC
  k = 20,000,000
  Price: 2000 USDC/ETH

Trader Action: Swap 10 ETH for USDC
  Input: 10 ETH
  Fee: 0.03 ETH (0.3%)
  Effective Input: 9.97 ETH

Post-Swap State:
  Reserve X: 109.97 ETH
  Reserve Y: 181,876 USDC (calculated from k invariant)
  Output: 18,124 USDC
  Effective Price: 1812.4 USDC/ETH (9.4% slippage)
  New Pool Price: 1653.5 USDC/ETH
```

### Collateralized Lending Protocols and Interest Rate Dynamics

Compound Finance pioneered the DeFi lending primitive by constructing on-chain money markets where users deposit assets into protocol-managed pools, receiving interest-bearing cTokens that accrue yield algorithmically. Borrowers post collateral to mint cTokens, then borrow against that collateral up to a protocol-defined loan-to-value ratio. The system operates without maturity dates or negotiated terms—interest accrues continuously per Ethereum block, and positions remain open indefinitely until the borrower repays or falls below the collateralization threshold triggering liquidation.

The interest rate mechanism governs capital allocation across the protocol's money markets. Compound employs a utilization-based rate model where borrowing costs rise nonlinearly as the pool's utilization ratio $u = \frac{\text{Borrows}}{\text{Cash} + \text{Borrows}}$ approaches 100%. The borrow rate function implements a kinked formula:

$$r_{\text{borrow}} = \begin{cases} r_0 + u \cdot r_1 & \text{if } u \leq u_{\text{optimal}} \\ r_0 + u_{\text{optimal}} \cdot r_1 + (u - u_{\text{optimal}}) \cdot r_2 & \text{if } u > u_{\text{optimal}} \end{cases}$$

Typical parameterizations set $u_{\text{optimal}} = 0.8$ with gentle slope $r_1 = 0.04$ below the kink and steep slope $r_2 = 0.75$ above. This design maintains reasonable borrowing costs under normal conditions but imposes punitive rates above 80% utilization to incentivize repayment or new supply, preventing the pool from approaching 100% utilization where withdrawal liquidity vanishes. The supply rate earned by depositors equals the borrow rate multiplied by utilization, minus a protocol reserve factor:

$$r_{\text{supply}} = u \cdot r_{\text{borrow}} \cdot (1 - \text{reserve factor})$$

This creates a natural spread where the protocol captures 10-20% of interest as reserves while depositors earn 80-90% of the weighted borrowing costs. At 80% utilization with 5% borrow rate, depositors earn approximately 3.6% while borrowers pay 5%, and the protocol retains 0.4% in reserves.

Collateralization requirements prevent undercollateralized borrowing and systemic default risk. Each asset receives a collateral factor between 0% and 90% set by protocol governance based on liquidity and volatility characteristics. Ethereum typically receives 82.5% collateral factor, meaning a user depositing $10,000 of ETH can borrow up to $8,250 of other assets. Stablecoins receive lower factors around 75% despite lower volatility because their primary use case as collateral involves leveraged long positions in volatile assets. The protocol calculates a user's account liquidity by summing collateral value adjusted by factors and subtracting total borrows:

$$\text{Account Liquidity} = \sum_i (\text{Collateral}_i \times \text{Price}_i \times \text{Factor}_i) - \sum_j (\text{Borrow}_j \times \text{Price}_j)$$

When account liquidity turns negative, the position becomes undercollateralized and subject to liquidation. External liquidators can repay up to 50% of the borrowed amount, receiving the borrower's collateral at a discount typically set to 8%. This liquidation incentive ensures swift position closure during price crashes while penalizing borrowers who fail to maintain adequate collateral buffers.

Aave extends Compound's model with additional features including flash loans, variable versus stable rate borrowing options, and collateral delegation. The flash loan primitive allows anyone to borrow unlimited amounts with zero collateral, provided the loan is repaid within the same atomic transaction. This enables capital-efficient arbitrage strategies, collateral swapping, and self-liquidation mechanisms. A user can flash borrow 10,000 ETH, execute a complex DeFi arbitrage across Uniswap, Curve, and Balancer, and repay the loan plus a 0.09% fee, all within a single transaction costing only gas fees. If any step fails, the entire transaction reverts atomically, eliminating default risk.

```text
Compound Liquidation Scenario:

Initial Position:
  Collateral: 10 ETH @ $2000 = $20,000
  Collateral Factor: 82.5%
  Borrow Capacity: $16,500
  Borrowed: 15,000 USDC
  Health Factor: 1.10 (110% collateralized)

Price Crash: ETH drops to $1600
  Collateral Value: $16,000
  Borrow Capacity: $13,200
  Borrowed: 15,000 USDC
  Health Factor: 0.88 (88% collateralized - UNDERCOLLATERALIZED)

Liquidator Action:
  Repays: 7,500 USDC (50% of borrowed amount)
  Receives: 4.95 ETH ($7,920 worth of collateral at $1600/ETH)
  Liquidation Bonus: 8% ($720 profit)
  
Post-Liquidation:
  Remaining Collateral: 5.05 ETH = $8,080
  Remaining Borrow: 7,500 USDC
  Health Factor: 1.11 (restored to safety)
```

### Stablecoin Mechanisms and Peg Maintenance

Stablecoins solve the unit-of-account problem in cryptocurrency markets by constructing synthetic assets pegged to external reference prices, typically the US dollar. Three distinct architectural approaches have emerged: fiat-collateralized stablecoins backed 1:1 by bank reserves, crypto-collateralized stablecoins overcollateralized by volatile assets, and algorithmic stablecoins that maintain pegs through reflexive supply adjustments without direct collateral backing.

MakerDAO pioneered the crypto-collateralized model with DAI, a decentralized stablecoin generated by depositing ETH or other approved collateral into Maker Vaults at minimum 150% collateralization ratios. A user locking $15,000 of ETH can mint up to 10,000 DAI, paying a stability fee (effectively an interest rate) to maintain the position. The stability fee adjusts dynamically based on DAI's market price—when DAI trades below $1, the fee increases to incentivize debt repayment and reduce supply, while fees decrease when DAI trades above $1 to encourage new minting. This negative feedback mechanism theoretically maintains the peg through supply contraction and expansion, though it operates with significant lag and requires governance intervention during extreme dislocations.

The system remains solvent through aggressive liquidation of undercollateralized vaults. When ETH price drops and a vault's collateralization ratio falls below 150%, keepers (automated liquidation bots) can trigger Dutch auctions where the collateral sells for DAI at a starting premium that decreases over time until buyers emerge. The vault owner pays a 13% liquidation penalty, creating strong incentive to maintain collateralization buffers above the minimum threshold. During the March 2020 crash when ETH dropped 50% in 24 hours, cascading liquidations resulted in some collateral auctions completing at $0 due to network congestion preventing keeper participation, leaving MakerDAO with $4 million in undercollateralized debt that required emergency issuance of MKR governance tokens to recapitalize.

Algorithmic stablecoins attempt to maintain pegs without collateral by implementing reflexive mechanisms linking the stablecoin to a volatile base asset. Terra's UST implemented a burn-mint arbitrage where users could always exchange 1 UST for $1 worth of LUNA (Terra's volatile native token) through the protocol regardless of market prices. When UST traded at $0.98, arbitrageurs could buy UST on the open market and redeem it for $1 of LUNA, pocketing 2% profit while absorbing UST supply and pushing the price toward peg. Conversely, when UST traded at $1.02, users could burn $1 of LUNA to mint 1 UST and sell at profit, expanding supply and lowering the price. This mechanism worked effectively during growth phases when LUNA appreciated, as the system's ability to absorb UST supply expanded with LUNA market cap.

The fatal flaw emerged during reflexive collapse scenarios. When confidence in the peg falters and UST holders rush to exit, the redemption mechanism floods the market with newly minted LUNA, crashing its price and thereby reducing the system's capacity to absorb further UST supply. This creates a death spiral where UST depegging accelerates LUNA issuance, which crashes LUNA price, which further depegs UST. In May 2022, this dynamic vaporized $40 billion in combined UST and LUNA market capitalization over 72 hours as the peg broke, LUNA supply inflated from 350 million to 6.5 trillion tokens, and both assets approached zero. The collapse demonstrated that algorithmic stablecoins without external collateral backing are fundamentally vulnerable to bank run dynamics, as the peg maintenance mechanism becomes the attack vector during coordinated redemption cascades.

Modern stablecoin designs converge toward hybrid models combining elements of collateralization with algorithmic supply adjustment. Frax implements a fractional reserve model where USDC provides partial backing while algorithmic mechanisms manage the remainder. Liquity's LUSD maintains 110% ETH collateralization with interest-free loans but implements redemption mechanisms where LUSD can always be swapped for $1 of ETH from the lowest-collateralized trove, creating a hard price floor. These architectures recognize that pure algorithmic pegs face existential risk during market stress while pure collateralized models sacrifice capital efficiency.

```text
Stablecoin Peg Maintenance Mechanisms:

MakerDAO (Crypto-Collateralized):
  Peg Defense: Stability fee adjustment (supply/demand)
  Collateral: ETH, WBTC, stablecoins (150%+ collateralization)
  Risk: Liquidation cascades during sharp price drops
  Capital Efficiency: Low (1.5x overcollateralization)

Terra UST (Algorithmic - Failed):
  Peg Defense: LUNA burn-mint arbitrage
  Collateral: None (reflexive backing only)
  Risk: Death spiral during bank runs
  Capital Efficiency: High (no collateral requirement)
  Failure Mode: May 2022 depeg → LUNA hyperinflation → total collapse

Frax (Hybrid):
  Peg Defense: Fractional USDC backing + algorithmic supply
  Collateral: ~90% USDC backing + FXS governance token
  Risk: Partial exposure to bank run dynamics
  Capital Efficiency: Medium (adjustable collateral ratio)
```

## 3. High-Performance Optimization & Failure Modes

### Capital Efficiency and Liquidity Mining Incentive Design

DeFi protocols compete on capital efficiency—the ability to generate returns per unit of deployed capital. Uniswap V2's full-range liquidity provision is capital inefficient because most liquidity sits far from current market prices, earning no fees. V3's concentrated liquidity addresses this by allowing providers to allocate capital within tight ranges where trading activity concentrates, but introduces active management overhead. Sophisticated LPs deploy automated rebalancing strategies that adjust positions dynamically as prices move, maintaining exposure within optimal fee-earning ranges while minimizing impermanent loss.

Liquidity mining programs distribute governance tokens to incentivize TVL growth, but create mercenary capital dynamics where participants chase highest yields without long-term protocol alignment. A lending protocol offering 50% APY through token rewards attracts deposits until the diluted token price reduces real yields, at which point capital migrates to the next highest yielder. Sustainable protocols transition from inflationary token emissions toward fee-based revenue models where actual economic activity rather than subsidized yields supports returns. Uniswap generates $1-2 million daily in organic trading fees distributed to LPs without token incentives, demonstrating product-market fit independent of artificial yield subsidies.

The optimal capital allocation strategy for lending protocols involves recursive borrowing where users deposit assets, borrow against them at lower rates than deposit yield, and redeposit the borrowed assets in a loop. During periods when COMP token rewards exceeded borrowing costs, users could deposit ETH earning 2% supply rate plus 8% COMP rewards, borrow USDC at 3% cost while earning 6% COMP rewards, and redeposit the USDC for compounding returns. This recursive leverage maxes out at the collateral factor limit, creating 5-10x effective exposure to token rewards. Such strategies work until token prices correct or protocol parameters adjust to eliminate the spread, frequently leaving late entrants with underwater leveraged positions.

### Liquidation Cascades and Systemic Risk Propagation

DeFi's composability creates systemic fragility where stress in one protocol propagates through the dependency graph. Consider a leveraged yield farmer who deposits ETH into Aave, borrows USDC, swaps for more ETH on Uniswap, and redeposits into Aave for additional borrowing capacity. A 30% ETH price drop triggers liquidation in Aave, flooding Uniswap with forced ETH sales, further depressing price and triggering additional liquidations in a cascade. The May 2021 event saw $4 billion liquidated across lending protocols in 24 hours as ETH dropped from $4000 to $1850, with gas prices spiking to 2000 gwei and preventing many users from adding collateral to save positions.

Liquidation mechanisms must balance competing objectives: swift position closure to protect protocol solvency versus gradual execution to minimize market impact and maximize recovery value for borrowers. Compound's fixed 50% liquidation limit with 8% bonus creates cliff effects where positions experience sudden 8% losses rather than gradual margin calls. Aave implements variable liquidation bonuses (5-15%) based on asset liquidity and risk parameters, while Liquity uses a two-tier system where positions below 110% collateralization face instant liquidation while those between 110-150% can be redeemed against gradually. Market-based liquidation auctions (Dutch or English) theoretically achieve better price discovery than fixed discount mechanisms but introduce latency and execution risk during volatile conditions.

The oracle problem compounds liquidation risk. DeFi protocols rely on price feeds from Chainlink or Uniswap TWAP oracles, which introduce lag between actual market prices and on-chain reported prices. During flash crashes, spot prices may deviate 20-30% from oracle prices for 1-5 minutes, creating arbitrage opportunities where traders trigger liquidations based on stale prices and immediately flip the collateral at profit in external markets. Oracle manipulation attacks where attackers artificially move price feeds through large trades in low-liquidity pools have extracted tens of millions from DeFi protocols, prompting migration toward decentralized oracle networks with multiple data sources and manipulation-resistant aggregation.

### Flash Loan Attack Vectors and Economic Exploits

Flash loans transform DeFi security from a technical problem into an economic problem. Traditional hacks require stealing private keys or exploiting smart contract bugs. Flash loan attacks exploit economic assumptions where protocols naively trust oracle prices or assume certain invariants hold between transactions. In a typical attack, the attacker flash borrows millions from Aave, uses the capital to manipulate a price oracle by executing massive swaps in a low-liquidity pool, triggers a protocol action (borrowing, liquidation, or governance vote) based on the manipulated price, extracts value, and repays the flash loan, all within one atomic transaction.

The February 2020 bZx exploit demonstrated this attack class. The attacker flash borrowed 10,000 ETH from dYdX, used 5,500 ETH to open a 5x leveraged ETH short on bZx, dumped the remaining 4,500 ETH for sUSD on Kyber to manipulate the sUSD price oracle, and then closed the bZx short at the artificially favorable rate, extracting $350,000 profit. No smart contract bug existed—the attack exploited bZx's reliance on Kyber's spot price as an oracle without sufficient liquidity depth or TWAP smoothing. Subsequent attacks on Harvest Finance ($24M), Cream Finance ($130M), and dozens of others follow similar patterns: flash loan for capital → manipulate price oracle → exploit protocol logic → profit.

Defenses against flash loan attacks require time-weighted average price oracles, liquidity depth thresholds, and multi-block transaction requirements. Uniswap V2's TWAP oracle accumulates price observations across blocks, making manipulation expensive because attackers must maintain artificial prices for multiple blocks rather than within a single transaction. Protocols can check whether a price feed has sufficient liquidity by requiring minimum reserve sizes before trusting oracle data. Governance actions can enforce time delays where proposals must wait multiple blocks before execution, preventing single-transaction attacks. However, these defenses increase latency and reduce capital efficiency, creating fundamental tradeoffs between security and performance in DeFi protocol design.

### Regulatory Encroachment and Decentralization Theater

The legal status of DeFi protocols occupies regulatory gray area as authorities extend securities law and banking regulations into blockchain-based financial systems. The question centers on whether protocol developers and token holders constitute issuers or operators of unregistered securities and money transmission businesses. Uniswap Labs faced SEC scrutiny over whether UNI token constitutes an investment contract and whether the protocol operates as an unlicensed exchange. Lending protocols question whether they perform banking activities requiring money transmitter licenses. Stablecoin issuers face direct regulatory pressure, with USDC and USDT subject to bank-like oversight while algorithmic stablecoins face existential questions about whether they constitute unregistered securities.

Many protocols respond through decentralization theater—creating appearances of decentralization while maintaining effective centralized control. A protocol may implement time-locked admin keys that can pause contracts or upgrade logic, issue governance tokens that concentrate in early investor hands, or rely on centralized infrastructure for price feeds and off-chain components. True decentralization requires immutable contracts with no admin keys, broadly distributed governance token ownership, and elimination of single points of failure in oracle and infrastructure dependencies. Liquity and Reflexer achieve this standard by deploying immutable contracts with no admin access and limited governance scope, but sacrifice upgradability and adaptive parameter tuning.

The regulatory future likely segments DeFi into compliant and non-compliant layers. Compliant protocols implement KYC/AML checks, geographic restrictions, and regulatory reporting, accepting reduced censorship resistance in exchange for legal clarity. Non-compliant protocols pursue maximum decentralization and censorship resistance, accepting permanent regulatory hostility and limited fiat on-ramps. Users navigate between layers through privacy-preserving bridges and decentralized identity systems, creating a two-tier financial system where compliant protocols provide fiat connectivity while non-compliant protocols provide uncensored access to financial primitives. The long-term question is whether this bifurcation can survive increasing state pressure to close the compliant-to-non-compliant bridges and force all financial activity into regulated channels.
