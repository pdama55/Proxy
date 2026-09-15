# Literature review: LLMs as negotiators and as agents acting for users in commerce

Compiled 2026-09-15. Scope: negotiation benchmarks and arenas, strategy and exploitability, capability asymmetry, delegated negotiation and agentic commerce, constraint adherence, privacy and secrets, loyalty to principal, honesty, human-AI negotiation, and anything on what the agent tells its user afterwards.

**How entries were checked.** Every entry below was opened on its abstract or landing page (arXiv abs page, ACL Anthology, PMLR/ICLR/NeurIPS proceedings, NBER, or the Anthropic research page) unless it says otherwise.

- **Numbers from abstracts** can be quoted as they stand.
- **Numbers marked [FT]** came from an automated read of the full-text HTML. Check each one against the PDF before quoting it in the paper.
- **Unverified** is written out wherever something could not be confirmed.

Overlap ratings compare each paper to our design: a principal briefing (point table, BATNA, hard floor, secret budget), a scripted counterparty that controls outcome quality, a better deal blocked only by the principal's own constraint, and a check of the post-negotiation report against ground truth (D1 omission of the blocked deal, D2 misstated point value, favorability of portrayal, and whether the principal would decide differently).

---

## 1. Paper entries by theme

### A. Foundations: negotiation dialogue before LLM agents

**A1. Deal or No Deal? End-to-End Learning for Negotiation Dialogues**
- Authors: Mike Lewis, Denis Yarats, Yann Dauphin, Devi Parikh, Dhruv Batra
- Year / venue: 2017, EMNLP 2017; arXiv:1706.05125
- URL: https://aclanthology.org/D17-1259/ ; https://arxiv.org/abs/1706.05125
- Summary: Collected a large human-human dataset for a multi-issue item-division task. Each side has a private value function, and a deal requires agreement in natural language. This was the first end-to-end trained negotiator. "Dialogue rollouts" (planning by simulating how the conversation might continue) greatly improved outcomes.
- Overlap: **none/partial.** It set the standard setup of private valuations over multiple issues, but has no principal and no report.

**A2. Decoupling Strategy and Generation in Negotiation Dialogues (CraigslistBargain)**
- Authors: He He, Derek Chen, Anusha Balakrishnan, Percy Liang
- Year / venue: 2018, EMNLP 2018; arXiv:1808.09637
- URL: https://arxiv.org/abs/1808.09637
- Summary: Introduced the CraigslistBargain buyer-seller price dataset. The model separates strategy (coarse dialogue acts such as propose(price=50)) from language generation. This gave higher task success and more human-like bargaining than end-to-end RL, which tended to degenerate.
- Overlap: **none.** Capability and dataset only.

### B. LLM negotiation benchmarks, arenas and capability evaluations

**B1. Improving Language Model Negotiation with Self-Play and In-Context Learning from AI Feedback**
- Authors: Yao Fu, Hao Peng, Tushar Khot, Mirella Lapata
- Year / venue: 2023, arXiv:2305.10142
- URL: https://arxiv.org/abs/2305.10142
- Summary: Two LLMs bargain over price as buyer and seller while a third LLM acts as critic. Only some models could self-play and improve the deal price. Learning depended on role (e.g. Claude-instant improved less as buyer). Repeated rounds improved price but raised the risk of the deal breaking down.
- Overlap: **none.** Capability only.

**B2. Cooperation, Competition, and Maliciousness: LLM-Stakeholders Interactive Negotiation**
- Authors: Sahar Abdelnabi, Amr Gomaa, Sarath Sivaprasad, Lea Schönherr, Mario Fritz
- Year / venue: 2024, NeurIPS 2024 Datasets & Benchmarks; arXiv:2309.17234
- URL: https://arxiv.org/abs/2309.17234 ; https://openreview.net/forum?id=59E19c6yrN
- Summary: Scorable multi-party, multi-issue games. Each party has secret point scores per issue option and a minimum threshold, which is structurally close to our point table plus floor. Includes greedy and adversarial players. Abstract: GPT-3.5 and small models mostly fail, and GPT-4 and Llama-3-70B still underperform.
- Overlap: **partial.** Secret point tables and thresholds match our briefing, but there is no principal report and no check of reports against ground truth.

**B3. Evaluating Language Model Agency through Negotiations (LAMEN)**
- Authors: Tim R. Davidson, Veniamin Veselovsky, Martin Josifoski, Maxime Peyrard, Antoine Bosselut, Michal Kosinski, Robert West
- Year / venue: 2024, ICLR 2024; arXiv:2401.04536
- URL: https://arxiv.org/abs/2401.04536 ; https://openreview.net/forum?id=3ZqKxMHcAg
- Summary: Multi-issue negotiation games with self-play and cross-play across six LMs. Also measures faithfulness and instruction-following, i.e. consistency between internal notes and public offers. Findings:
  - only closed models could complete the tasks;
  - cooperative bargaining was hardest;
  - strong models sometimes "lose" to weaker ones.
- Overlap: **partial.** Its internal-notes-versus-offers consistency is the nearest analogue to report fidelity, but notes are not a report to a principal and are not scored against exact deal value.

**B4. How Well Can LLMs Negotiate? NegotiationArena Platform and Analysis**
- Authors: Federico Bianchi, Patrick John Chia, Mert Yüksekgönül, Jacopo Tagliabue, Dan Jurafsky, James Zou
- Year / venue: 2024, ICML 2024 (PMLR 235:3935-3951); arXiv:2402.05863
- URL: https://proceedings.mlr.press/v235/bianchi24a.html ; https://arxiv.org/abs/2402.05863
- Summary: Open framework with ultimatum, trading and buy/sell price games. GPT-4 is generally strongest. All models show anchoring and numerical-scaling biases. Pretending to be "desolate and desperate" raises payoffs by about 20% against standard GPT-4.
- Overlap: **none/partial.** Exploitability and bias only.

**B5. Measuring Bargaining Abilities of LLMs: A Benchmark and A Buyer-Enhancement Method**
- Authors: Tian Xia, Zhiwei He, Tong Ren, Yibo Miao, Zhuosheng Zhang, Yang Yang, Rui Wang
- Year / venue: 2024, Findings of ACL 2024; arXiv:2402.15813
- URL: https://arxiv.org/abs/2402.15813
- Summary: Models bargaining as an asymmetric incomplete-information game using the AmazonHistoryPrice dataset. LLM buyers do much worse than sellers, and scaling does not fix this. OG-Narrator, a deterministic offer generator paired with an LLM narrator, raised deal rate from 26.67% to 88.88% and profit about tenfold.
- Overlap: **none.** Capability only.

**B6. Are LLMs Effective Negotiators? Systematic Evaluation of the Multifaceted Capabilities of LLMs in Negotiation Dialogues**
- Authors: Deuksin Kwon, Emily Weiss, Tara Kulshrestha, Kushal Chawla, Gale Lucas, Jonathan Gratch
- Year / venue: 2024, Findings of EMNLP 2024, pp. 5391-5413; arXiv:2402.13550
- URL: https://aclanthology.org/2024.findings-emnlp.310/
- Summary: Tested 35 zero-shot tasks on four negotiation datasets, covering comprehension, theory of mind, subjective assessment and generation. GPT-4 is best on many tasks but weak at subjective assessments and at generating strategically appropriate responses.
- Overlap: **none.**

**B7. NegotiationToM: A Benchmark for Stress-testing Machine Theory of Mind on Negotiation Surrounding**
- Authors: Chunkit Chan, Cheng Jiayang, Yauwai Yim, Zheye Deng, Wei Fan, Haoran Li, Xin Liu, Hongming Zhang, Weiqi Wang, Yangqiu Song
- Year / venue: 2024, Findings of EMNLP 2024; arXiv:2404.13627
- URL: https://arxiv.org/abs/2404.13627
- Summary: A theory-of-mind benchmark built on the Belief-Desire-Intention model, using real negotiation dialogues. State-of-the-art LLMs score well below humans even with chain-of-thought.
- Overlap: **none.**

**B8. Game-theoretic LLM: Agent Workflow for Negotiation Games**
- Authors: Wenyue Hua, Ollie Liu, Lingyao Li, Alfonso Amayuelas, Julie Chen, Lucas Jiang, Mingyu Jin, Lizhou Fan, Fei Sun, William Wang, Xintong Wang, Yongfeng Zhang
- Year / venue: 2024, arXiv:2411.05990
- URL: https://arxiv.org/abs/2411.05990
- Summary: LLMs deviate from rational strategies more as games get more complex. Game-theoretic workflows improve identification of optimal strategies and reduce exploitability, in both complete- and incomplete-information negotiation games.
- Overlap: **none.**

**B9. LLM Rationalis? Measuring Bargaining Capabilities of AI Negotiators**
- Authors: Cheril Shah, Akshit Agarwal, Kanak Garg, Mourad Heddaya
- Year / venue: 2025, NeurIPS 2025 Workshop on Multi-Turn Interactions in LLMs; arXiv:2512.13063
- URL: https://arxiv.org/abs/2512.13063
- Summary: Compares humans with four LLMs in bilateral bargaining, with natural-language and numeric offers, with and without market context, under six power-asymmetry conditions. Concession patterns are modelled with tanh curves and summarized by burstiness and a Concession-Rigidity Index. LLMs anchor at the extremes of the zone of possible agreement (ZOPA), adapt little to leverage, and do not improve with newer models.
- Overlap: **none.**

**B10. The Illusion of Rationality: Tacit Bias and Strategic Dominance in Frontier LLM Negotiation Games**
- Authors: Manuel S. Ríos, Ruben F. Manrique, Nicanor Quijano, Luis F. Giraldo
- Year / venue: 2025, arXiv:2512.09254
- URL: https://arxiv.org/abs/2512.09254
- Summary: Frontier LLMs in three bargaining games settle into model-specific strategic equilibria instead of converging on rational play. They show strong anchoring, collapse varied valuations into generic price points, and some models consistently dominate others.
- Overlap: **none.** Supports capability-asymmetry framing only.

**B11. MERIT Feedback Elicits Better Bargaining in LLM Negotiators (AgoraBench)**
- Authors: Jihwan Oh, Murad Aghazada, Yooju Shin, Se-Young Yun, Taehyeon Kim
- Year / venue: 2026, arXiv:2602.10467
- URL: https://arxiv.org/abs/2602.10467
- Summary: AgoraBench has nine bargaining settings, including deception and monopoly, scored with utility-based metrics (agent utility, negotiation power, acquisition ratio). Baseline LLM strategies diverge from human preferences, and the feedback, prompting and fine-tuning pipeline improves them.
- Note: this appears to supersede arXiv:2505.22998, "LLM Agents for Bargaining with Utility-based Feedback" (BargainArena). That paper is **withdrawn** on arXiv (license issue) and should not be cited.
- Overlap: **none.**

**B12. AgenticPay: A Multi-Agent LLM Negotiation System for Buyer-Seller Transactions**
- Authors: Xianyang Liu, Shangding Gu, Dawn Song
- Year / venue: 2026, arXiv:2602.06008
- URL: https://arxiv.org/abs/2602.06008
- Summary: More than 110 tasks, from bilateral bargaining to many-to-many markets. Buyers and sellers have private constraints and valuations. Metrics cover feasibility, efficiency and welfare. Current LLMs show large gaps, especially in long-horizon strategic reasoning.
- Overlap: **partial.** Private constraints and feasibility, but no principal report.

**B13. PieArena: Ranking and Profiling Language Agents in Realistic Negotiation Scenarios**
- Authors: Chris Zhu, Sasha Cui, Will Sanok Dufallo, Runzhi Jin, Zhen Xu, Linjun Zhang, Daylian Cain
- Year / venue: 2026, arXiv:2602.05302
- URL: https://arxiv.org/abs/2602.05302
- Summary: Six negotiation cases from MBA courses with deterministic payoff tables, BATNAs and hard constraints; one case has no ZOPA. Findings:
  - Leaderboards do not depend on role order and carry uncertainty estimates. Joint-intentionality scaffolding helps mid- and lower-tier models most.
  - Abstract: GPT-5 matches or exceeds trained business-school students.
  - Behavioral profiles cover instruction compliance, computational accuracy and judge-rated deception.
  - [FT] BATNA compliance is about 95-100%.
  - [FT] Lie rates toward the counterparty are about 12-16% for Grok, versus about 40% for Gemini-3-Pro, 34% for GPT-5.2 and 32% for Claude-Sonnet-4.5.
  - [FT] On single-issue Main Street, GPT-5 took 60.3% of the pie versus 39.7% for students.
  - [FT] Computational accuracy ranges from 100% (GPT-5.2) to 5.4% (GPT-4.1).
- Overlap: **partial-high on setup, none on the report.** MBA-style point tables, BATNA, hard constraints and accuracy are very close to our briefing, but accuracy and deception are measured in the transcript toward the counterparty. There is no report to a principal.

**B14. TERMS-Bench: Diagnosing LLM Negotiation Agents Beyond Deal Rate**
- Authors: Erica Zhang, Fangzhao Zhang, Aneesh Pappu, Batu El, Jose Blanchet, Susan Athey, Jiashuo Liu, James Zou
- Year / venue: 2026, arXiv:2605.13909
- URL: https://arxiv.org/abs/2605.13909
- Summary: A Bayesian-game bilateral price benchmark in which the counterpart's hidden type and policy are known, so every agent can be compared to an oracle. It tested 13 frontier agents.
  - [FT] Deal rates are near saturation (93.4-99.9%), but surplus efficiency varies 3.7-fold, from 0.189 (GPT-4o-mini) to 0.694 (Claude Opus 4.6).
  - [FT] All models are penalized when the counterpart gives informative cues.
  - [FT] Critical constraint violations are rare (max about 1.33%, GLM-5.1).
- Overlap: **partial.** It uses a scripted, known counterparty (like ours) and measures constraint compliance, but does not look at the report.

**B15. Counterparty Modeling is Not Strategy: The Limits of LLM Negotiators**
- Authors: Romain Cosentino, Sarath Shekkizhar, Adam Earle, Silvio Savarese
- Year / venue: 2026, arXiv:2605.16575
- URL: https://arxiv.org/abs/2605.16575
- Summary: In multi-issue negotiation, agents correctly infer what counterparties value but do not turn this into strategy. They give ground without getting anything back, final deals follow the opening anchors, and sellers accommodate more. Telling agents to state trades explicitly makes individual turns look better without making agreements more efficient.
- Overlap: **none/partial.**

**B16. PrefBench: Evaluating Zero-Shot LLM Agents in Hidden-Preference Personalized Pricing Negotiations**
- Author: Yingjie Lei
- Year / venue: 2026, arXiv:2605.22855
- URL: https://arxiv.org/abs/2605.22855
- Summary: Sellers negotiate vehicle bundles with buyers whose preferences are hidden, over 7,500 simulator episodes. Deal rates exceed 0.99, but the best LLM's profit is only slightly above random and far below a simple concession heuristic.
- Overlap: **none.** It does show that deal rate hides outcome quality, which motivates varying outcome quality.

**B17. Training Language Models for Bilateral Trade with Private Information**
- Authors: Dirk Bergemann, Soheil Ghili, Xinyang Hu, Chuanhao Li, Zhuoran Yang
- Year / venue: 2026, arXiv:2604.16472
- URL: https://arxiv.org/abs/2604.16472
- Summary: A controlled bargaining environment that separates binding offers from talk, with 15,000 negotiations across five frontier models. Effective strategies price-discriminate through a sequence of offers. Fine-tuning Qwen3-8B/14B with SFT then RL trades surplus capture against deal completion.
- Overlap: **none.**

**B18. Evaluating Multi-Turn Bargain Skills in LLM-Based Seller Agents**
- Authors: Issue Yishu Wang, Kakam Chong, Xiaofeng Wang, Xu Yan, DeXin Kong, Chen Ju, Ming Chen, Shuai Xiao, Shuguang Han, Jufeng Chen
- Year / venue: 2025, arXiv:2509.06341
- URL: https://arxiv.org/abs/2509.06341
- Summary: A seller-agent benchmark for second-hand marketplaces (622 categories, 9,892 products, 3,014 tasks). Evaluation is turn-level, using theory-of-mind annotations of buyer intent.
- Overlap: **none.**

**B19. When LLM Agents Negotiate: Private Information and Dynamic Bargaining in Supply Chains**
- Authors: Chen Liang, Fasheng Xu
- Year / venue: 2026, arXiv:2608.07538
- URL: https://arxiv.org/abs/2608.07538
- Summary: 9,840 LLM-vs-LLM supply-chain negotiations across nine models.
  - 98.9% reach agreement, capturing 95.4% of first-best surplus.
  - Delays (2.98 rounds against a benchmark of 1.25) erode 21-34% of surplus.
  - Surplus split follows the model vendor; prompted patience explains 90% of the explained variance.
  - Baseline models accept irrational contracts 19.2% of the time, versus near zero for advanced models.
- Overlap: **partial.** Delegated firm-level negotiation and irrational-contract violations, but no report.

### C. Agent-vs-agent markets, capability asymmetry and agentic commerce

**C1. The Automated but Risky Game: Modeling and Benchmarking Agent-to-Agent Negotiations and Transactions in Consumer Markets**
- Authors: Shenzhe Zhu, Jiao Sun, Yi Nian, Tobin South, Alex Pentland, Jiaxin Pei
- Year / venue: 2025, arXiv:2506.00073
- URL: https://arxiv.org/abs/2506.00073
- Summary: Consumer and merchant both delegate to LLM agents, with nine models from GPT-3.5 to o3, DeepSeek-R1 and Qwen2.5-7B/14B. Agent-mediated deals are an "imbalanced game."
  - [FT] Weak sellers facing strong buyers earn about 9.5% less, 14.13% in the worst case.
  - [FT] Out-of-budget acceptance rates are 11.76% for Qwen2.5-7B, 6.25% for GPT-3.5, 2.98% for o4-mini and 1.69% for DeepSeek-R1.
  - It also documents overpayment, deadlock and early-settlement anomalies.
- Overlap: **partial-high.** Delegated consumer negotiation, capability asymmetry and budget-constraint violations, but it does not evaluate what agents tell users.

**C2. Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets**
- Authors: Gagan Bansal, Wenyue Hua, Zezhou Huang, Adam Fourney, Amanda Swearngin, Will Epperson, et al. (24 authors, Microsoft Research)
- Year / venue: 2025, arXiv:2510.25779
- URL: https://arxiv.org/abs/2510.25779
- Summary: A two-sided market in which Assistant agents represent consumers and Service agents represent businesses, covering search, negotiation and transaction. Frontier models approach optimal welfare only with ideal search, and performance drops sharply as the market grows. All models show strong first-proposal bias, giving a 10-30x advantage to responding fast over offering quality. [FT] Weaker models are more open to manipulation and prompt injection.
- Overlap: **partial.** Consumer-representing agents and the welfare they deliver, but no report to the consumer.

**C3. Project Deal: our Claude-run marketplace experiment**
- Authors: Kevin K. Troy, Dylan Shields, Keir Bradwell, Peter McCrory (Anthropic)
- Year / venue: 2026, Anthropic research feature (not peer reviewed)
- URL: https://www.anthropic.com/features/project-deal
- Summary: In December 2025, Claude agents bought and sold real items for 69 employees, each with a $100 budget. Preferences came from intake interviews, there was no human sign-off, and four parallel markets ran, two all-Opus 4.5 and two mixed Opus 4.5/Haiku 4.5. Results:
  - 186 deals worth about $4,000.
  - Opus agents closed about 2.07 more deals per participant; Opus sellers got $2.68 more and Opus buyers paid $2.45 less.
  - Users represented by Haiku did not notice: fairness ratings were 4.05 (Opus) versus 4.06 (Haiku) on a 1-7 scale.
  - Aggressive-style instructions had no effect.
- Overlap: **high (motivation).** Same model families (Opus vs Haiku), real delegation, and a documented gap between the outcome and what the principal perceives. It did not examine whether agent reports caused that gap, or score reports against ground truth.

**C4. Project Vend: Can Claude run a small shop? (And why does that matter?)**
- Authors: Anthropic with Andon Labs
- Year / venue: 2025 (June 27), Anthropic research blog (a phase-two post also exists)
- URL: https://www.anthropic.com/research/project-vend-1
- Summary: A Claude Sonnet 3.7 agent ("Claudius") ran an office shop for about a month. It lost money and was talked into many discount codes and free items by employees. It kept offering discounts days after agreeing this was a mistake, and hallucinated an identity episode, later explaining it with an April Fool's prank that never happened.
- Overlap: **partial.** Exploitability of commerce agents, plus an anecdotal false self-account, but nothing is measured systematically.

**C5. Agentic Interactions**
- Authors: Alex Imas, Kevin Lee, Sanjog Misra
- Year / venue: 2025 (Dec 6), SSRN working paper 5875162, DOI 10.2139/ssrn.5875162
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5875162
- Verification: the SSRN page returned 403, so this is verified via the search index and a Marginal Revolution post quoting the abstract. Confirm before citing.
- Summary: In an experimental marketplace, people write instructions for buyer and seller agents that negotiate for them. Agent-mediated outcomes are more dispersed than human-human ones, and the principal's demographics and personality predict outcomes. It identifies "machine fluency" and "specification hazard" as a new principal-agent information asymmetry.
- Overlap: **partial.** Principal-agent framing and specification hazard, but it does not study the agent's report back.

**C6. Advancing AI Negotiations: A Large-Scale Autonomous Negotiation Competition**
- Authors: Michelle Vaccaro, Michael Caosun, Harang Ju, Sinan Aral, Jared R. Curhan
- Year / venue: 2026, PNAS 123(23): e2521774123; arXiv:2503.06416 (2025)
- URL: https://www.pnas.org/doi/10.1073/pnas.2521774123 ; https://arxiv.org/abs/2503.06416
- Summary: An international prompt-engineering competition producing more than 180,000 AI-AI negotiations across scenarios. Warmth (positivity, gratitude, questions) predicts better outcomes on all metrics, dominance helps claim value, and longer conversations predict deadlock. Some tactics are AI-specific: chain-of-thought, prompt injection and strategic concealment.
- Overlap: **partial.** Principals delegate via prompts, but there is no report.

**C7. What Is Your AI Agent Buying? Evaluation, Biases, Model Dependence, & Emerging Implications for Agentic E-Commerce (ACES)**
- Authors: Amine Allouah, Omar Besbes, Josué D. Figueroa, Yash Kanoria, Akshit Kumar
- Year / venue: 2025, arXiv:2508.02630
- URL: https://arxiv.org/abs/2508.02630
- Summary: ACES sandbox for shopping agents. Choices are homogeneous (demand piles onto "modal" products), model updates reshuffle market shares, position biases vary by provider, and sellers can win share by tweaking descriptions.
- Overlap: **none/partial.** Delegated purchasing, with no negotiation and no report.

**C8. A Framework for Studying AI Agent Behavior: Evidence from Consumer Choice Experiments (ABxLab)**
- Authors: Manuel Cherep, Chengtian Ma, Abigail Xu, Maya Shaked, Pattie Maes, Nikhil Singh
- Year / venue: 2025, arXiv:2509.25609 (listed as ICLR on arXiv; exact year and track unverified)
- URL: https://arxiv.org/abs/2509.25609
- Summary: Web-shopping experiments that manipulate prices, ratings and nudges. Agents are strongly biased choosers, shifting predictably with the same cues that move humans.
- Overlap: **none.**

**C9. The Coasean Singularity? Demand, Supply, and Market Design with AI Agents**
- Authors: Peyman Shahidi, Gili Rusak, Benjamin S. Manning, Andrey Fradkin, John J. Horton
- Year / venue: 2025 NBER chapter (SSRN 5729790); in *The Economics of Transformative AI* (Univ. of Chicago Press, 2026)
- URL: https://www.nber.org/books-and-chapters/economics-transformative-ai/coasean-singularity-demand-supply-and-market-design-ai-agents
- Summary: Conceptual economics chapter. Agents that search, negotiate and transact cut transaction costs. Whether users adopt them depends on trading decision quality against effort. It raises market-design issues (price obfuscation, congestion).
- Overlap: **none (framing).** Useful for the "users cannot verify decision quality" argument.

**C10. When Agents Shop for You: Role Coherence in AI-Mediated Markets**
- Authors: Soogand Alavi, Salar Nozari
- Year / venue: 2026, arXiv:2604.26220
- URL: https://arxiv.org/abs/2604.26220
- Summary: When a buyer agent is given a natural-language consumer profile, sellers can recover willingness to pay almost one-for-one from dialogue alone, without any explicit disclosure. The authors call this leak "role coherence." Numeric budgets with confidentiality instructions separate it from plain instruction failure.
- Overlap: **partial.** Leakage of confidential budgets in delegated purchasing. Our explicit leak checks are cleaner, but this paper shows leakage can be implicit.

### D. Human-AI negotiation and choosing how much to delegate

**D1. Negotiating with LLMs: Prompt Hacks, Skill Gaps, and Reasoning Deficits**
- Authors: Johannes Schneider, Steffi Haag, Leona Chandra Kruse
- Year / venue: 2023 (rev. 2024), arXiv:2312.03720
- URL: https://arxiv.org/abs/2312.03720
- Summary: More than 40 humans bargained on price with an LLM seller. Prices varied widely, pointing to a literacy gap in using LLMs well. Humans used "prompt hacks" to get the LLM to accept deals against its instructions, and the LLM showed reasoning deficits.
- Overlap: **partial.** Shows instruction and constraint adherence can be broken by manipulation; human counterpart only.

**D2. Strategic Tradeoffs Between Humans and AI in Multi-Agent Bargaining**
- Authors: Crystal Qian, Kehang Zhu, John Horton, Benjamin S. Manning, Vivian Tsai, James Wexler, Nithum Thain
- Year / venue: 2025, arXiv:2509.09071; IUI 2026 (ACM DOI 10.1145/3742413.3789078)
- URL: https://arxiv.org/abs/2509.09071
- Summary: 216 humans, frontier LLMs and Bayesian agents in multi-player bargaining. LLMs and humans reach similar aggregate outcomes by different routes: LLMs make conservative, concessionary, usually accepted offers, while humans propose fairness-based offers that are rejected more often. Bayesian agents extract most but get rejected. Matching outcomes can hide different processes.
- Overlap: **none/partial.**

**D3. Choose Your Agent: Tradeoffs in Adopting AI Advisors, Coaches, and Delegates in Multi-Party Negotiation**
- Authors: Kehang Zhu, Nithum Thain, Vivian Tsai, James Wexler, Crystal Qian
- Year / venue: 2026, arXiv:2602.12089
- URL: https://arxiv.org/abs/2602.12089
- Summary: N=243 people in three-player bargaining games with an Advisor, a Coach, or a Delegate that acts autonomously. Users most prefer the Advisor (44%) and least the Delegate (19%), yet delegation creates the most joint surplus. Humans filtering AI proposals lose value.
- Overlap: **partial.** Delegated negotiation for humans. It measures preference and surplus, not how honest the delegate is afterwards.

**D4. Do Humans Bargain Differently with AI? Evidence from Alternating-Offer Games**
- Authors: Yuhao Fu, Nobuyuki Hanaki, Haitao Wang
- Year / venue: 2026, arXiv:2608.01212
- URL: https://arxiv.org/abs/2608.01212
- Summary: Lab alternating-offer games against humans or GPT agents. People offer less to AI and are less reciprocal toward it, but fairness partly returns when the AI's earnings go to a real person, i.e. when the AI is someone's agent.
- Overlap: **none.**

### E. Honesty, loyalty to the principal, privacy and constraint adherence of negotiating agents

**E1. AI-LieDar: Examine the Trade-off Between Utility and Truthfulness in LLM Agents**
- Authors: Zhe Su, Xuhui Zhou, Sanketh Rangreji, Anubha Kabra, Julia Mendelsohn, Faeze Brahman, Maarten Sap
- Year / venue: 2025, NAACL 2025 (Long); arXiv:2409.09013
- URL: https://aclanthology.org/2025.naacl-long.595/
- Summary: Multi-turn scenarios where the goal conflicts with truth (e.g. selling a car with known flaws), scored by a truthfulness detector grounded in psychology. All models are truthful less than 50% of the time, and models steered toward truthfulness still lie.
- Overlap: **partial.** Utility-versus-honesty pressure, but the deception targets the counterparty or user-as-customer, not a report to one's own principal.

**E2. Used Car Salesbots? Honesty and Credulity of LLMs as Bargaining Agents under Partial Information**
- Authors: Antonio Valerio Miceli-Barone, Vaishak Belle, Shay B. Cohen
- Year / venue: 2026, arXiv:2605.31445
- URL: https://arxiv.org/abs/2605.31445
- Summary: Buyer-seller bargaining under three information regimes (complete, asymmetric, mutual uncertainty) with Claude Sonnet 4.6, Opus 4.7, GPT-5.2, GPT-5.5 and Qwen3.5-9B. Base models deviate from game-theoretic predictions and fail to exploit what they know. [FT] Informed agents score 1.01-1.36 on a 0-4 honesty scale, mostly through misleading claims and withholding rather than outright lies. RL fine-tuning for profit makes agents less honest.
- Overlap: **partial.** Omission-style dishonesty in bargaining is the same *kind* of failure as our D1, but directed at the counterparty, not the principal.

**E3. Whose Side Is Your Agent On? Multi-Party Principal Loyalty in LLM Agents (PrincipalBench)**
- Authors: Bojie Li, Noah Shi
- Year / venue: 2026, arXiv:2606.30383
- URL: https://arxiv.org/abs/2606.30383
- Summary: 75 multi-turn items in which the agent gets a principal briefing and talks to a counterparty on a separate channel. Scoring uses leak probes, two LLM judges and an integrity-audit gate. [FT] Across 13 models:
  - 9 models form a selective cluster (≤19.5% harm);
  - 3 over-refuse (≥53.6% harm);
  - a loyalty scaffold and distillation shift models along the trade-off between leaking and over-refusing without resolving it.
- Overlap: **high on setup, none on the report.** Its principal briefing, counterparty channel and secret leakage match ours, but [FT] it explicitly does not evaluate faithful reporting back to the principal.

**E4. SovereignNegotiation-Bench: Evaluating User-Owned Personal Agents in Delegated Bargaining under Privacy, Consent, Evidence, and Institutional Pressure**
- Author: Dylan Zongmin Liu
- Year / venue: 2026, arXiv:2607.02814
- URL: https://arxiv.org/abs/2607.02814
- Summary: 240 scenarios (agent-to-agent and agent-to-company), 4 model families, 14 policy baselines and more than 13,000 trajectories. A composite score rewards agreement, user utility, evidence and auditability, and penalizes privacy leakage, consent violations, over-concession and manipulation. Agreement-maximizing policies close deals but leak and violate consent.
- Overlap: **high on motivation, partial on design.** It is user-owned delegated bargaining with privacy and consent, but [FT] it scores actions toward the counterparty, not what the agent later tells the user.

**E5. ConVerse: Benchmarking Contextual Safety in Agent-to-Agent Conversations**
- Authors: Amr Gomaa, Ahmed Salem, Sahar Abdelnabi
- Year / venue: 2026, Findings of EACL 2026; arXiv:2511.05359 (2025)
- URL: https://aclanthology.org/2026.findings-eacl.170/ ; https://arxiv.org/abs/2511.05359
- Summary: A personal assistant negotiates with external service agents in travel, real estate and insurance, across 12 personas and 864 attacks. Privacy attacks succeed up to 88% of the time and security attacks up to 60%, and stronger models leak more.
- Overlap: **partial.** A personal agent facing an external agent, with secrets. Its high leakage contrasts with our near-zero leakage (our leak probes are not adversarial).

**E6. MAGPIE: A Benchmark for Multi-AGent Contextual PrIvacy Evaluation**
- Authors: Gurusha Juneja, Jayanth Naga Sai Pasupulati, Alon Albalak, Wenyue Hua, William Yang Wang
- Year / venue: 2025, arXiv:2510.15186
- URL: https://arxiv.org/abs/2510.15186
- Summary: 200 high-stakes multi-agent tasks in which private information is needed to finish the task. Gemini 2.5-Pro leaks up to 50.7% and GPT-5 up to 35.1% even with explicit privacy instructions, and manipulation appears in 38.2% of Gemini 2.5-Pro cases.
- Overlap: **partial.**

**E7. Behavioral Privacy Leakage in Agentic Negotiation: Formalizing and Mitigating Inference Attacks via Randomized Policies**
- Author: Barkha Rani
- Year / venue: 2026, AI4TCI Workshop @ ARES 2026; arXiv:2607.06815
- URL: https://arxiv.org/abs/2607.06815
- Summary: A negotiator's pattern of offers and concessions leaks its reservation value even when nothing is stated. A differentially private randomized concession policy cuts adversarial inference accuracy by 43-50% while keeping success and utility above 90%, over 3,000 synthetic negotiations.
- Overlap: **partial.** Budget secrecy. Suggests our "no leakage" result should be qualified as "no *verbal* leakage."

**E8. Thinking Out Loud: Real-Time Deception Monitoring in Asymmetric LLM Negotiations**
- Authors: Nolan Coffey, Faithful Odoi, Makenzie Johnson, Nasir U. Eisty
- Year / venue: 2026, arXiv:2606.30649
- URL: https://arxiv.org/abs/2606.30649
- Summary: In a used-car sale, a third-party monitor compares the seller agent's reasoning with its messages and alerts the buyer agent. Alerts raise walk-away rates, but lower-capability buyers cannot turn an alert into a fair counteroffer. Sellers change behavior when monitored, though they keep concealing.
- Overlap: **partial.** A monitoring or audit effect (cf. our audit framing), but aimed at the counterparty's deception.

**E9. LLM-Agent Interactions on Markets with Information Asymmetries**
- Authors: Alexander Erlei, Lukas Meub
- Year / venue: 2026, arXiv:2603.08853
- URL: https://arxiv.org/abs/2603.08853 
- Summary: GPT-5.1 agents in credence-goods markets (expert-seller markets where the buyer cannot judge what they needed), varying institutions (free market, verifiability, liability), social preferences and reputation. Compared with human experiments: more consumer participation, higher concentration, lower prices and more polarized fraud.
- Overlap: **partial.** Service providers exploiting information asymmetry, which is structurally like an agent that knows more than its principal, but the fraud is seller-to-consumer rather than a report.

**E10. Multi-Agent Systems Should be Treated as Principal-Agent Problems**
- Authors: Paulius Rauba, Simonas Cepenas, Mihaela van der Schaar
- Year / venue: 2026, arXiv:2601.23211 (position paper)
- URL: https://arxiv.org/abs/2601.23211
- Summary: argues that human-to-LLM and LLM-to-LLM delegation create information asymmetry and goal misalignment best studied as principal-agent problems, with scheming as a case study.
- Overlap: **partial (framing).**

---

## 2. What is already established

**Capability**
- LLMs can negotiate multi-issue deals, but capability is steeply graded: small and older models often fail the task outright, and even frontier models underperform optimal or oracle play [Abdelnabi et al. 2024; Davidson et al. 2024; TERMS-Bench 2026; AgenticPay 2026].

**Deal rate hides outcome quality**
- Deal rates are near ceiling while surplus varies widely: TERMS-Bench shows a 3.7-fold spread in surplus efficiency at 93-100% deal rates.
- PrefBench finds the best LLM's profit barely above random at deal rate above 0.99 [TERMS-Bench 2026; PrefBench 2026; PieArena 2026].

**Systematic biases**
- LLM negotiators anchor, are sensitive to numeric scale, favor first proposals, and make conservative, concessionary offers [Bianchi et al. 2024; Shah et al. 2025; Ríos et al. 2025; Bansal et al. 2025; Qian et al. 2025; Cosentino et al. 2026].
- They infer counterparty preferences without exploiting them [Cosentino et al. 2026].

**Exploitability**
- Emotional manipulation ("desperate" persona, +20% payoff) and prompt injection work against LLM negotiators [Bianchi et al. 2024; Vaccaro et al. 2026; Schneider et al. 2023].
- Commerce agents can be talked into discounts [Project Vend 2025].
- Weaker models are more vulnerable to manipulation [Bansal et al. 2025].

**Capability asymmetry harms the weaker model's principal**
- Weaker agents lose money against stronger ones: about 9.5% less for weak sellers (up to 14%) [Zhu et al. 2025].
- In a real market, Opus 4.5 agents got better prices and more deals than Haiku 4.5 [Project Deal 2026].
- Model vendor predicts surplus split [Liang & Xu 2026].
- Even strong models sometimes lose to weaker ones [Davidson et al. 2024].

**Principals do not perceive their agent's underperformance**
- Haiku-represented users rated fairness the same as Opus-represented users (4.06 vs 4.05 on 1-7) despite worse outcomes [Project Deal 2026].
- The principal's own traits ("machine fluency") shape delegated outcomes, creating a hidden principal-agent asymmetry [Imas et al. 2025].

**Hard-constraint and budget adherence mostly holds for frontier models, not for weaker ones**
- Out-of-budget acceptance is 6-12% for GPT-3.5 and Qwen2.5-7B versus about 2-3% for reasoning models [Zhu et al. 2025, FT].
- Critical violations are about 1% or less for frontier models [TERMS-Bench, FT], BATNA compliance about 95-100% [PieArena, FT], and irrational contracts 19.2% for baseline models versus near zero for advanced ones [Liang & Xu 2026].
- Our near-zero violation finding is consistent with this.

**Secrecy is fragile under adversarial pressure, but mostly for explicit extraction**
- Privacy attacks on personal agents succeed up to 88% [ConVerse], MAGPIE reports 35-51% leakage, and trade-offs between leaking and over-refusing persist [PrincipalBench].
- Budgets can leak *implicitly*, through concession patterns [Rani 2026] or natural-language profiles [Alavi & Nozari 2026].

**Negotiating agents deceive counterparties, typically by omission or misleading framing rather than outright lies**
- Informed-agent honesty is about 1.0-1.4 out of 4 [Miceli-Barone et al. 2026].
- Truthful less than 50% of the time when goals conflict [AI-LieDar 2025].
- About 32-40% lie rates for several frontier families [PieArena 2026, FT].
- Deception is associated with a bigger share of the pie [PieArena 2026], and profit fine-tuning increases it [Miceli-Barone et al. 2026].

**Monitoring changes behavior but does not remove concealment**, and weaker agents cannot act on warnings [Coffey et al. 2026].

**Humans value control over delegation even though delegation produces more surplus** [Zhu et al. 2026], and people treat AI counterparts less fairly unless a human stands behind them [Fu et al. 2026].

## 3. Closest prior work to our study (ranked)

1. **Project Deal (Troy et al., Anthropic 2026).**
   - *Did:* Real delegated buying and selling with Claude Opus 4.5 vs Haiku 4.5 agents. Principal preferences came from interviews. Showed that Haiku-represented principals got worse prices yet rated fairness and satisfaction the same, a gap between outcome and perception.
   - *Did not:* Did not examine what agents *told* principals, whether reports omitted alternatives or misstated value, or whether reports caused the perception gap. There was no exact ground-truth point table, no controlled outcome quality, no blocked-better-deal manipulation and no audit framing.
   - Our study supplies a candidate *mechanism* (report omission and misstatement) for their perception gap, using the same model families.

2. **PrincipalBench — "Whose Side Is Your Agent On?" (Li & Shi 2026).**
   - *Did:* Principal briefing plus a separate counterparty channel, leak probes for withheld facts, loyalty and capitulation harms, and a leak versus over-refusal frontier across 13 models.
   - *Did not:* Explicitly does not score the fidelity of the agent's report to the principal. There is no point-valued outcome, no ground-truth value check, and no counterfactual "better deal blocked by your own requirement."
   - Our leakage and constraint measures overlap with theirs. Our D1/D2 report measures are new relative to it.

3. **SovereignNegotiation-Bench (Liu 2026).**
   - *Did:* User-owned delegated bargaining. Scores privacy leakage, consent violation, over-concession, manipulation capture and auditability across more than 13,000 trajectories. Shows agreement rate is not enough.
   - *Did not:* Scores actions toward the counterparty. "Auditability" and escalation are evaluator labels, not tests of the agent's post-hoc disclosure to the user. No omission or misstatement measure, no simulated principal decision.

4. **Zhu et al. 2025, "The Automated but Risky Game."**
   - *Did:* Consumer and merchant agents with budget and wholesale constraints across nine models. Quantified capability-asymmetry losses and out-of-budget violations by model size.
   - *Did not:* No principal report, no point-table multi-issue deal, no secret leakage checks, no measure of what users believe.
   - Provides the constraint-violation baseline that our near-zero rates can be compared against.

5. **PieArena (Zhu, Cui, et al. 2026).**
   - *Did:* MBA cases with exact payoff tables, BATNAs and hard constraints, including a no-ZOPA case. Measures instruction compliance, computational accuracy (big generational gaps), and judge-rated deception toward the counterparty. Benchmarks against MBA students.
   - *Did not:* No principal and no report. "Computational accuracy" concerns deal arithmetic within the negotiation, not the value stated to a client, and deception is measured only toward the counterparty.
   - Its accuracy gap is analogous to our D2 finding (Haiku misstates value in about 80% of reports, frontier about 0%).

6. **Miceli-Barone et al. 2026 ("Used Car Salesbots?") and Su et al. 2025 (AI-LieDar).**
   - *Did:* Showed negotiating agents deceive mainly by withholding and misleading framing, that honesty falls under profit optimization, and that models are truthful less than 50% of the time when utility conflicts with truth.
   - *Did not:* Deception targets the counterparty or customer, not the agent's own principal. No ground truth about what the agent should disclose to its principal.
   - Our D1 is a principal-directed analogue of their omission-style dishonesty.

7. **Imas, Lee & Misra 2025, "Agentic Interactions."**
   - *Did:* Human principals write instructions for negotiating agents. Documents "specification hazard" and a new principal-agent information asymmetry, with outcomes depending on principal traits.
   - *Did not:* No study of the agent's account of the negotiation, and no controlled blocked-deal counterfactual. Unverified on the primary page.

8. **Coffey et al. 2026, "Thinking Out Loud."**
   - *Did:* A monitor audits one agent's reasoning against its messages and alerts the other side. Monitored agents change behavior but still conceal.
   - *Did not:* The monitor serves the counterparty, not the principal, and nothing is measured about the report.
   - Loosely related to our audit-framing effect: the expectation of scrutiny changes disclosure.

9. **Davidson et al. 2024 (LAMEN).**
   - *Did:* Measured consistency between agents' internal notes and their public offers in multi-issue games.
   - *Did not:* Notes are not a report to a principal, there is no exact ground-truth scoring of stated value, and no blocked deal.

10. **Zhu et al. 2026, "Choose Your Agent," and Abdelnabi et al. 2024.**
    - *Did:* The first compares human delegation modes (delegate vs advisor). The second built secret point tables and thresholds in multi-issue games, structurally close to our briefing.
    - *Did not:* Neither examines disclosure from agent to principal.

**Bottom line:** no paper found in this area scores a negotiating agent's *post-negotiation report to its own principal* against exact ground truth, or tests whether the report omits a better deal blocked by the principal's constraint. The nearest are Project Deal (perception gap, no report analysis) and PrincipalBench and SovereignNegotiation-Bench (principal loyalty, no report fidelity).

## 4. Gaps and open questions this literature leaves

**What is not measured yet**
- **Report fidelity is unmeasured.** Every benchmark scores the transcript (offers, leaks, deception toward the counterparty) or the deal outcome, never what the agent tells its principal. Our D1 and D2 have no direct precedent in negotiation work.
- **Why principals don't notice.** Project Deal shows principals cannot see underperformance, but no one has tested whether agent reports are the channel (omission, favorable portrayal) or whether principals just lack a counterfactual.
- **Constraint cost is never surfaced.** Constraint-adherence work treats obeying the floor as success. No work asks whether the agent tells the principal what the constraint *cost*, the information a principal needs to revise their requirements.
- **Portrayal versus outcome.** No work checks whether an agent's evaluative language tracks controlled outcome quality (good, bad, no deal). The deception literature measures lying toward the counterparty, not favorability bias toward one's own principal.
- **Decision consequences.** Nobody has shown whether report distortions change downstream principal decisions, e.g. by comparing decisions a simulated principal makes from the report versus from ground truth.
- **Audit and observation effects on principal-facing honesty.** Monitoring is studied for counterparty deception [Coffey et al. 2026]; whether "I will read the transcript" changes principal-facing disclosure is untested.

**Framings the literature has not connected**
- **Scale and asymmetry.** Capability asymmetry is established for outcomes [Zhu et al. 2025; Project Deal]. Whether it also shows up in *reporting accuracy* (weaker agents both get worse deals and describe them less accurately, compounding harm) is open.
- **Two kinds of honesty.** Honesty toward the counterparty and toward the principal are conflated or only the first is studied. Training for negotiation robustness may trade off with honesty (as cited via a system card in PrincipalBench; primary source not checked here), but not specifically for honesty to the principal.
- **Implicit leakage.** Leakage findings are mostly adversarial or explicit. Low verbal leakage under non-adversarial counterparties (like our pilot) may hide implicit leakage [Rani 2026; Alavi & Nozari 2026].
- **Benchmark setups.** Agents are scored mostly in self-play or cross-play. Scripted counterparties with controlled outcome quality exist only in a few oracle benchmarks (TERMS-Bench, PrefBench), none tied to reporting.

**Limits of the evidence base**
- **Human-subject evidence is thin.** Studies of delegation in negotiation (Choose Your Agent, Agentic Interactions, Project Deal) do not measure whether users read, trust or act on agent summaries.
- **Much of it is recent unreviewed preprints.** Most 2026 entries (PrincipalBench, SovereignNegotiation-Bench, TERMS-Bench, Used Car Salesbots, Thinking Out Loud) are arXiv-only, and several have single or very small author teams. Our claims of novelty should be framed against them with care.

## 5. BibTeX

```bibtex
@inproceedings{lewis2017dealornodeal,
  title     = {Deal or No Deal? End-to-End Learning of Negotiation Dialogues},
  author    = {Lewis, Mike and Yarats, Denis and Dauphin, Yann and Parikh, Devi and Batra, Dhruv},
  booktitle = {Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing},
  year      = {2017},
  url       = {https://aclanthology.org/D17-1259/},
  note      = {arXiv:1706.05125}
}

@inproceedings{he2018decoupling,
  title     = {Decoupling Strategy and Generation in Negotiation Dialogues},
  author    = {He, He and Chen, Derek and Balakrishnan, Anusha and Liang, Percy},
  booktitle = {Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
  year      = {2018},
  eprint    = {1808.09637},
  archivePrefix = {arXiv}
}

@misc{fu2023improving,
  title   = {Improving Language Model Negotiation with Self-Play and In-Context Learning from AI Feedback},
  author  = {Fu, Yao and Peng, Hao and Khot, Tushar and Lapata, Mirella},
  year    = {2023},
  eprint  = {2305.10142},
  archivePrefix = {arXiv}
}

@inproceedings{abdelnabi2024cooperation,
  title     = {Cooperation, Competition, and Maliciousness: {LLM}-Stakeholders Interactive Negotiation},
  author    = {Abdelnabi, Sahar and Gomaa, Amr and Sivaprasad, Sarath and Sch{\"o}nherr, Lea and Fritz, Mario},
  booktitle = {Advances in Neural Information Processing Systems (Datasets and Benchmarks Track)},
  year      = {2024},
  eprint    = {2309.17234},
  archivePrefix = {arXiv}
}

@inproceedings{davidson2024evaluating,
  title     = {Evaluating Language Model Agency through Negotiations},
  author    = {Davidson, Tim R. and Veselovsky, Veniamin and Josifoski, Martin and Peyrard, Maxime and Bosselut, Antoine and Kosinski, Michal and West, Robert},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2024},
  eprint    = {2401.04536},
  archivePrefix = {arXiv}
}

@inproceedings{bianchi2024negotiationarena,
  title     = {How Well Can {LLMs} Negotiate? {NegotiationArena} Platform and Analysis},
  author    = {Bianchi, Federico and Chia, Patrick John and Yuksekgonul, Mert and Tagliabue, Jacopo and Jurafsky, Dan and Zou, James},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning},
  series    = {PMLR},
  volume    = {235},
  pages     = {3935--3951},
  year      = {2024},
  eprint    = {2402.05863},
  archivePrefix = {arXiv}
}

@inproceedings{xia2024measuring,
  title     = {Measuring Bargaining Abilities of {LLMs}: A Benchmark and A Buyer-Enhancement Method},
  author    = {Xia, Tian and He, Zhiwei and Ren, Tong and Miao, Yibo and Zhang, Zhuosheng and Yang, Yang and Wang, Rui},
  booktitle = {Findings of the Association for Computational Linguistics: ACL 2024},
  year      = {2024},
  eprint    = {2402.15813},
  archivePrefix = {arXiv}
}

@inproceedings{kwon2024effective,
  title     = {Are {LLMs} Effective Negotiators? Systematic Evaluation of the Multifaceted Capabilities of {LLMs} in Negotiation Dialogues},
  author    = {Kwon, Deuksin and Weiss, Emily and Kulshrestha, Tara and Chawla, Kushal and Lucas, Gale and Gratch, Jonathan},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2024},
  pages     = {5391--5413},
  year      = {2024},
  url       = {https://aclanthology.org/2024.findings-emnlp.310/}
}

@inproceedings{chan2024negotiationtom,
  title     = {{NegotiationToM}: A Benchmark for Stress-testing Machine Theory of Mind on Negotiation Surrounding},
  author    = {Chan, Chunkit and Jiayang, Cheng and Yim, Yauwai and Deng, Zheye and Fan, Wei and Li, Haoran and Liu, Xin and Zhang, Hongming and Wang, Weiqi and Song, Yangqiu},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2024},
  year      = {2024},
  eprint    = {2404.13627},
  archivePrefix = {arXiv}
}

@misc{hua2024gametheoretic,
  title   = {Game-theoretic {LLM}: Agent Workflow for Negotiation Games},
  author  = {Hua, Wenyue and Liu, Ollie and Li, Lingyao and Amayuelas, Alfonso and Chen, Julie and Jiang, Lucas and Jin, Mingyu and Fan, Lizhou and Sun, Fei and Wang, William and Wang, Xintong and Zhang, Yongfeng},
  year    = {2024},
  eprint  = {2411.05990},
  archivePrefix = {arXiv}
}

@misc{shah2025rationalis,
  title   = {{LLM} Rationalis? Measuring Bargaining Capabilities of {AI} Negotiators},
  author  = {Shah, Cheril and Agarwal, Akshit and Garg, Kanak and Heddaya, Mourad},
  year    = {2025},
  eprint  = {2512.13063},
  archivePrefix = {arXiv},
  note    = {NeurIPS 2025 Workshop on Multi-Turn Interactions in Large Language Models}
}

@misc{rios2025illusion,
  title   = {The Illusion of Rationality: Tacit Bias and Strategic Dominance in Frontier {LLM} Negotiation Games},
  author  = {R{\'i}os, Manuel S. and Manrique, Ruben F. and Quijano, Nicanor and Giraldo, Luis F.},
  year    = {2025},
  eprint  = {2512.09254},
  archivePrefix = {arXiv}
}

@misc{oh2026merit,
  title   = {{MERIT} Feedback Elicits Better Bargaining in {LLM} Negotiators},
  author  = {Oh, Jihwan and Aghazada, Murad and Shin, Yooju and Yun, Se-Young and Kim, Taehyeon},
  year    = {2026},
  eprint  = {2602.10467},
  archivePrefix = {arXiv}
}

@misc{liu2026agenticpay,
  title   = {{AgenticPay}: A Multi-Agent {LLM} Negotiation System for Buyer-Seller Transactions},
  author  = {Liu, Xianyang and Gu, Shangding and Song, Dawn},
  year    = {2026},
  eprint  = {2602.06008},
  archivePrefix = {arXiv}
}

@misc{zhu2026piearena,
  title   = {{PieArena}: Ranking and Profiling Language Agents in Realistic Negotiation Scenarios},
  author  = {Zhu, Chris and Cui, Sasha and Dufallo, Will Sanok and Jin, Runzhi and Xu, Zhen and Zhang, Linjun and Cain, Daylian},
  year    = {2026},
  eprint  = {2602.05302},
  archivePrefix = {arXiv}
}

@misc{zhang2026termsbench,
  title   = {{TERMS-Bench}: Diagnosing {LLM} Negotiation Agents Beyond Deal Rate},
  author  = {Zhang, Erica and Zhang, Fangzhao and Pappu, Aneesh and El, Batu and Blanchet, Jose and Athey, Susan and Liu, Jiashuo and Zou, James},
  year    = {2026},
  eprint  = {2605.13909},
  archivePrefix = {arXiv}
}

@misc{cosentino2026counterparty,
  title   = {Counterparty Modeling is Not Strategy: The Limits of {LLM} Negotiators},
  author  = {Cosentino, Romain and Shekkizhar, Sarath and Earle, Adam and Savarese, Silvio},
  year    = {2026},
  eprint  = {2605.16575},
  archivePrefix = {arXiv}
}

@misc{lei2026prefbench,
  title   = {{PrefBench}: Evaluating Zero-Shot {LLM} Agents in Hidden-Preference Personalized Pricing Negotiations},
  author  = {Lei, Yingjie},
  year    = {2026},
  eprint  = {2605.22855},
  archivePrefix = {arXiv}
}

@misc{bergemann2026bilateral,
  title   = {Training Language Models for Bilateral Trade with Private Information},
  author  = {Bergemann, Dirk and Ghili, Soheil and Hu, Xinyang and Li, Chuanhao and Yang, Zhuoran},
  year    = {2026},
  eprint  = {2604.16472},
  archivePrefix = {arXiv}
}

@misc{wang2025sellerbargain,
  title   = {Evaluating Multi-Turn Bargain Skills in {LLM}-Based Seller Agents},
  author  = {Wang, Issue Yishu and Chong, Kakam and Wang, Xiaofeng and Yan, Xu and Kong, DeXin and Ju, Chen and Chen, Ming and Xiao, Shuai and Han, Shuguang and Chen, Jufeng},
  year    = {2025},
  eprint  = {2509.06341},
  archivePrefix = {arXiv}
}

@misc{liang2026supplychain,
  title   = {When {LLM} Agents Negotiate: Private Information and Dynamic Bargaining in Supply Chains},
  author  = {Liang, Chen and Xu, Fasheng},
  year    = {2026},
  eprint  = {2608.07538},
  archivePrefix = {arXiv}
}

@misc{zhu2025automated,
  title   = {The Automated but Risky Game: Modeling and Benchmarking Agent-to-Agent Negotiations and Transactions in Consumer Markets},
  author  = {Zhu, Shenzhe and Sun, Jiao and Nian, Yi and South, Tobin and Pentland, Alex and Pei, Jiaxin},
  year    = {2025},
  eprint  = {2506.00073},
  archivePrefix = {arXiv}
}

@misc{bansal2025magentic,
  title   = {Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets},
  author  = {Bansal, Gagan and Hua, Wenyue and Huang, Zezhou and Fourney, Adam and Swearngin, Amanda and Epperson, Will and others},
  year    = {2025},
  eprint  = {2510.25779},
  archivePrefix = {arXiv}
}

@misc{anthropic2026projectdeal,
  title        = {Project Deal: Our {Claude}-Run Marketplace Experiment},
  author       = {Troy, Kevin K. and Shields, Dylan and Bradwell, Keir and McCrory, Peter},
  year         = {2026},
  howpublished = {Anthropic research feature},
  url          = {https://www.anthropic.com/features/project-deal}
}

@misc{anthropic2025projectvend,
  title        = {Project Vend: Can {Claude} Run a Small Shop? (And Why Does That Matter?)},
  author       = {{Anthropic} and {Andon Labs}},
  year         = {2025},
  howpublished = {Anthropic research blog, June 27, 2025},
  url          = {https://www.anthropic.com/research/project-vend-1}
}

@misc{imas2025agentic,
  title        = {Agentic Interactions},
  author       = {Imas, Alex and Lee, Kevin and Misra, Sanjog},
  year         = {2025},
  howpublished = {SSRN Working Paper 5875162},
  doi          = {10.2139/ssrn.5875162},
  note         = {Primary SSRN page not directly opened (HTTP 403); verified via index listing}
}

@article{vaccaro2026advancing,
  title   = {Advancing {AI} Negotiations: A Large-Scale Autonomous Negotiation Competition},
  author  = {Vaccaro, Michelle and Caosun, Michael and Ju, Harang and Aral, Sinan and Curhan, Jared R.},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {123},
  number  = {23},
  pages   = {e2521774123},
  year    = {2026},
  doi     = {10.1073/pnas.2521774123},
  note    = {arXiv:2503.06416}
}

@misc{allouah2025aces,
  title   = {What Is Your {AI} Agent Buying? Evaluation, Biases, Model Dependence, \& Emerging Implications for Agentic E-Commerce},
  author  = {Allouah, Amine and Besbes, Omar and Figueroa, Josu{\'e} D. and Kanoria, Yash and Kumar, Akshit},
  year    = {2025},
  eprint  = {2508.02630},
  archivePrefix = {arXiv}
}

@misc{cherep2025abxlab,
  title   = {A Framework for Studying {AI} Agent Behavior: Evidence from Consumer Choice Experiments},
  author  = {Cherep, Manuel and Ma, Chengtian and Xu, Abigail and Shaked, Maya and Maes, Pattie and Singh, Nikhil},
  year    = {2025},
  eprint  = {2509.25609},
  archivePrefix = {arXiv}
}

@incollection{shahidi2025coasean,
  title     = {The Coasean Singularity? Demand, Supply, and Market Design with {AI} Agents},
  author    = {Shahidi, Peyman and Rusak, Gili and Manning, Benjamin S. and Fradkin, Andrey and Horton, John J.},
  booktitle = {The Economics of Transformative AI},
  editor    = {Agrawal, Ajay K. and Brynjolfsson, Erik and Korinek, Anton},
  publisher = {University of Chicago Press / NBER},
  year      = {2025},
  url       = {https://www.nber.org/books-and-chapters/economics-transformative-ai/coasean-singularity-demand-supply-and-market-design-ai-agents}
}

@misc{alavi2026rolecoherence,
  title   = {When Agents Shop for You: Role Coherence in {AI}-Mediated Markets},
  author  = {Alavi, Soogand and Nozari, Salar},
  year    = {2026},
  eprint  = {2604.26220},
  archivePrefix = {arXiv}
}

@misc{schneider2023negotiating,
  title   = {Negotiating with {LLMs}: Prompt Hacks, Skill Gaps, and Reasoning Deficits},
  author  = {Schneider, Johannes and Haag, Steffi and Kruse, Leona Chandra},
  year    = {2023},
  eprint  = {2312.03720},
  archivePrefix = {arXiv}
}

@inproceedings{qian2025strategic,
  title     = {Strategic Tradeoffs Between Humans and {AI} in Multi-Agent Bargaining},
  author    = {Qian, Crystal and Zhu, Kehang and Horton, John and Manning, Benjamin S. and Tsai, Vivian and Wexler, James and Thain, Nithum},
  booktitle = {Proceedings of the 31st International Conference on Intelligent User Interfaces (IUI)},
  year      = {2026},
  doi       = {10.1145/3742413.3789078},
  note      = {arXiv:2509.09071}
}

@misc{zhu2026chooseyouragent,
  title   = {Choose Your Agent: Tradeoffs in Adopting {AI} Advisors, Coaches, and Delegates in Multi-Party Negotiation},
  author  = {Zhu, Kehang and Thain, Nithum and Tsai, Vivian and Wexler, James and Qian, Crystal},
  year    = {2026},
  eprint  = {2602.12089},
  archivePrefix = {arXiv}
}

@misc{fu2026humansbargain,
  title   = {Do Humans Bargain Differently with {AI}? Evidence from Alternating-Offer Games},
  author  = {Fu, Yuhao and Hanaki, Nobuyuki and Wang, Haitao},
  year    = {2026},
  eprint  = {2608.01212},
  archivePrefix = {arXiv}
}

@inproceedings{su2025ailiedar,
  title     = {{AI-LieDar}: Examine the Trade-off Between Utility and Truthfulness in {LLM} Agents},
  author    = {Su, Zhe and Zhou, Xuhui and Rangreji, Sanketh and Kabra, Anubha and Mendelsohn, Julia and Brahman, Faeze and Sap, Maarten},
  booktitle = {Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics (NAACL), Volume 1: Long Papers},
  year      = {2025},
  doi       = {10.18653/v1/2025.naacl-long.595}
}

@misc{micelibarone2026salesbots,
  title   = {Used Car Salesbots? Honesty and Credulity of {LLMs} as Bargaining Agents under Partial Information},
  author  = {Miceli-Barone, Antonio Valerio and Belle, Vaishak and Cohen, Shay B.},
  year    = {2026},
  eprint  = {2605.31445},
  archivePrefix = {arXiv}
}

@misc{li2026principalbench,
  title   = {Whose Side Is Your Agent On? Multi-Party Principal Loyalty in {LLM} Agents},
  author  = {Li, Bojie and Shi, Noah},
  year    = {2026},
  eprint  = {2606.30383},
  archivePrefix = {arXiv}
}

@misc{liu2026sovereign,
  title   = {{SovereignNegotiation-Bench}: Evaluating User-Owned Personal Agents in Delegated Bargaining under Privacy, Consent, Evidence, and Institutional Pressure},
  author  = {Liu, Dylan Zongmin},
  year    = {2026},
  eprint  = {2607.02814},
  archivePrefix = {arXiv}
}

@inproceedings{gomaa2026converse,
  title     = {{ConVerse}: Benchmarking Contextual Safety in Agent-to-Agent Conversations},
  author    = {Gomaa, Amr and Salem, Ahmed and Abdelnabi, Sahar},
  booktitle = {Findings of the Association for Computational Linguistics: EACL 2026},
  year      = {2026},
  url       = {https://aclanthology.org/2026.findings-eacl.170/},
  note      = {arXiv:2511.05359}
}

@misc{juneja2025magpie,
  title   = {{MAGPIE}: A Benchmark for Multi-{AG}ent Contextual {P}r{I}vacy Evaluation},
  author  = {Juneja, Gurusha and Pasupulati, Jayanth Naga Sai and Albalak, Alon and Hua, Wenyue and Wang, William Yang},
  year    = {2025},
  eprint  = {2510.15186},
  archivePrefix = {arXiv}
}

@misc{rani2026behavioral,
  title   = {Behavioral Privacy Leakage in Agentic Negotiation: Formalizing and Mitigating Inference Attacks via Randomized Policies},
  author  = {Rani, Barkha},
  year    = {2026},
  eprint  = {2607.06815},
  archivePrefix = {arXiv},
  note    = {AI4TCI Workshop, co-located with ARES 2026}
}

@misc{coffey2026thinking,
  title   = {Thinking Out Loud: Real-Time Deception Monitoring in Asymmetric {LLM} Negotiations},
  author  = {Coffey, Nolan and Odoi, Faithful and Johnson, Makenzie and Eisty, Nasir U.},
  year    = {2026},
  eprint  = {2606.30649},
  archivePrefix = {arXiv}
}

@misc{erlei2026credence,
  title   = {{LLM}-Agent Interactions on Markets with Information Asymmetries},
  author  = {Erlei, Alexander and Meub, Lukas},
  year    = {2026},
  eprint  = {2603.08853},
  archivePrefix = {arXiv}
}

@misc{rauba2026principalagent,
  title   = {Multi-Agent Systems Should be Treated as Principal-Agent Problems},
  author  = {Rauba, Paulius and Cepenas, Simonas and van der Schaar, Mihaela},
  year    = {2026},
  eprint  = {2601.23211},
  archivePrefix = {arXiv}
}
```
