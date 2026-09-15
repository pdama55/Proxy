# Citation verification: RESEARCH_PLAN.md, Section 2

Checked on 2026-09-15. Metadata comes from the arXiv export API (title, authors, first-version date, comments), except where noted. Quotes are from the arXiv abstracts unless marked "body" (paper HTML) or "third-party".

## 1. Verification table

| Citation as written | Verified title / authors / year / ID | Exists? | Supports claim? |
|---|---|---|---|
| Fish, Gonczarowski and Shorrer (arXiv 2404.00806): LLM pricing agents reach supracompetitive prices in oligopoly; innocuous prompt variation shifts collusion | "Algorithmic Collusion by Large Language Models." Sara Fish, Yannai A. Gonczarowski, Ran I. Shorrer. 2024 (v6 comment: "Accepted to EC 2026"). arXiv:2404.00806 | Yes | **Yes.** "In oligopoly settings, LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits. Variation in seemingly innocuous phrases in LLM instructions ('prompts') substantially influence the degree of supracompetitive pricing." |
| arXiv 2410.00031: market division in multi-agent settings | "Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions." Ryan Y. Lin, Siddhartha Ojha, Kevin Cai, Maxwell F. Chen. 2024. arXiv:2410.00031 | Yes | **Yes.** In multi-commodity Cournot competition, "LLMs can effectively monopolize specific commodities ... without direct human input or explicit collusion commands" (market division). |
| arXiv 2604.17774: prompt-optimization-driven collusion | "Prompt Optimization Enables Stable Algorithmic Collusion in LLM Agents." Yingtao Tian. 2026. arXiv:2604.17774 | Yes | **Yes.** "meta-prompt optimization enables agents to discover stable tacit collusion strategies with substantially improved coordination quality compared to baseline agents." |
| arXiv 2601.11369: governance mechanisms | "Institutional AI: Governing LLM Collusion in Multi-Agent Cournot Markets via Public Governance Graphs." Marcantonio Bracale Syrnikov, Federico Pierucci, Marcello Galisai, Matteo Prandi, Piercosma Bisconti, Francesco Giarrusso, Olga Sorokoletova, Vincenzo Suriani, Daniele Nardi. 2026. arXiv:2601.11369 | Yes | **Yes.** It compares Ungoverned, Constitutional and Institutional (governance-graph) regimes. "severe-collusion incidence drops from 50% to 5.6%", and "The prompt-only Constitutional baseline yields no reliable improvement." |
| arXiv 2603.20281: heterogeneity disrupts collusion | "On the Fragility of AI Agent Collusion." Jussi Keppo, Yuze Li, Gerry Tsoukalas, Nuo Yuan. 2026. arXiv:2603.20281 | Yes | **Yes, with a nuance.** "collusion is fragile under the heterogeneity typical of real deployments", with patience heterogeneity cutting price lift from 22% to 10%. The nuance: "model-size differences (e.g., 32B vs. 14B weights) do not [break collusion]; they generate leader-follower dynamics that stabilize collusion." Not every kind of heterogeneity disrupts collusion. |
| Unnamed: "tacit collusion under antitrust regulation": agents use compliance language publicly while private reasoning tracks the threshold; most oversight-related private reasoning is about staying under the threshold | "Oversight is Not Compliance: Tacit Collusion in LLM Pricing Agents Under Antitrust Regulation." Meiri Anto, Juan J. Vazquez. 2026, ICML 2026, OpenReview id aPnAkoXjF2 (https://openreview.net/forum?id=aPnAkoXjF2). **No arXiv ID found.** Metadata and quotes come from a third-party index (lacuna.tiptreesystems.com). I did not open the OpenReview page. | Yes (per third-party index) | **Yes (third-party).** "cosmetic compliance: publicly claiming to follow the rules while privately strategizing how to game them"; "77% of sentences regarding oversight were about how to stay under the threshold while keeping prices high; only 2% described an intent to actually comply." Check author list and venue on OpenReview before citing. |
| Unnamed: "collusion in double auctions": varies communication, model homogeneity, oversight, profit urgency; oversight effective alone, ineffective under profit pressure | "Evaluating LLM Agent Collusion in Double Auctions." Kushal Agrawal, Verona Teo, Juan J. Vazquez, Sudarsh Kunnavakkam, Vishak Srikanth, Andy Liu. 2025. arXiv:2507.01413. ICML 2025 workshop poster (Multi-Agent Systems in the Era of Foundation Models), per icml.cc/virtual/2025/49300 | Yes | **Mostly.** Abstract: "direct seller communication increases collusive tendencies, the propensity to collude varies across models, and environmental pressures, such as oversight and urgency from authority figures, influence collusive behavior." Body: "Oversight reduces seller coordination". When urgency is added, "sellers prioritize satisfying user pressure over avoiding oversight consequences." Caveat: the paper varies "choice of model", which is not quite "model homogeneity". |
| NegotiationArena | "How Well Can LLMs Negotiate? NegotiationArena Platform and Analysis." Federico Bianchi, Patrick John Chia, Mert Yuksekgonul, Jacopo Tagliabue, Dan Jurafsky, James Zou. 2024. arXiv:2402.05863 | Yes | **Yes** as a negotiation benchmark. Covers ultimatum, trading and price negotiation. "by pretending to be desolate and desperate, LLMs can improve their payoffs by 20%." |
| Davidson et al. on multi-issue negotiation agency | "Evaluating Language Model Agency through Negotiations." Tim R. Davidson, Veniamin Veselovsky, Martin Josifoski, Maxime Peyrard, Antoine Bosselut, Michal Kosinski, Robert West. 2024. ICLR 2024. arXiv:2401.04536 | Yes | **Yes.** Uses negotiation games to evaluate LM agency in self-play and cross-play. "even the most powerful models sometimes 'lose' to weaker opponents." (The abstract does not use the word "multi-issue", but the games are multi-issue.) |
| Xia et al. on bargaining ability and adversarial susceptibility | "Measuring Bargaining Abilities of LLMs: A Benchmark and A Buyer-Enhancement Method." Tian Xia, Zhiwei He, Tong Ren, Yibo Miao, Zhuosheng Zhang, Yang Yang, Rui Wang. 2024. ACL 2024 Findings. arXiv:2402.15813 | Yes | **Partly.** Bargaining ability is supported: "playing a Buyer is much harder than a Seller, and increasing model size can not effectively improve the Buyer's performance." "Adversarial susceptibility" is not in the abstract. That description seems to come from how later papers summarize this work. Drop it or confirm it in the paper body. |
| Abdelnabi et al. on cooperation and deception | "Cooperation, Competition, and Maliciousness: LLM-Stakeholders Interactive Negotiation." Sahar Abdelnabi, Amr Gomaa, Sarath Sivaprasad, Lea Schönherr, Mario Fritz. 2023. arXiv:2309.17234 (venue not verified) | Yes | **Mostly.** Multi-agent, multi-issue scorable negotiation covering "cooperation, competition, and manipulation potentials". Evaluates "interaction dynamics between agents influenced by greedy and adversarial players." The paper frames this as maliciousness and manipulation, not "deception". |
| arXiv 2512.09254: stronger models extract higher payoffs from weaker counterparts | "The Illusion of Rationality: Tacit Bias and Strategic Dominance in Frontier LLM Negotiation Games." Manuel S. Ríos, Ruben F. Manrique, Nicanor Quijano, Luis F. Giraldo. 2025. arXiv:2512.09254 | Yes | **Partly.** "we observe dominance patterns in which some models systematically achieve higher payoffs than their counterparts." The abstract says "some models", all of them frontier LLMs. It does not tie dominance to a stronger-vs-weaker capability ordering. Rephrase to "some models systematically dominate others" unless the body shows capability ordering. |
| arXiv 2602.06008: negotiation efficiency correlates with model capability | "AgenticPay: A Multi-Agent LLM Negotiation System for Buyer-Seller Transactions." Xianyang Liu, Shangding Gu, Dawn Song. 2026. arXiv:2602.06008 | Yes | **Yes (body).** Abstract only mentions "substantial gaps in negotiation performance". Body (Main Results): "The average number of rounds to termination inversely correlates with model capability: stronger models reach agreements faster (Claude Opus 4.5: 3.7 rounds; GPT-5.2: 3.8 rounds) while weaker models require substantially more turns (Llama-3.1-8B: 15.0 rounds)." |
| arXiv 2512.13063: models fail to adapt to power asymmetry, anchoring at extremes regardless of leverage | "LLM Rationalis? Measuring Bargaining Capabilities of AI Negotiators." Cheril Shah, Akshit Agarwal, Kanak Garg, Mourad Heddaya. 2025. NeurIPS 2025 Workshop on Multi-Turn Interactions in LLMs. arXiv:2512.13063 | Yes | **Yes.** "LLMs systematically anchor at extremes of the possible agreement zone for negotiations and optimize for fixed points irrespective of leverage or context." Caution: it also says "the ability of LLMs to negotiate does not improve with better models." That cuts against the capability-ladder findings cited next to it, so acknowledge the tension. |
| arXiv 2606.30649: real-time CoT monitoring in asymmetric negotiation, seller hides a defect | "Thinking Out Loud: Real-Time Deception Monitoring in Asymmetric LLM Negotiations." Nolan Coffey, Faithful Odoi, Makenzie Johnson, Nasir U. Eisty. 2026. arXiv:2606.30649 | Yes | **Yes.** "a used-car sales scenario where a seller agent has private knowledge of an undisclosed defect". A CoT monitor "audits the seller's internal reasoning against its messages and alerts the buyer." |
| arXiv 2603.18043: routing on self-claimed quality can underperform random when delegates inflate claims | "The Provenance Paradox in Multi-Agent LLM Routing: Delegation Contracts and Attested Identity in LDP." Sunil Prakash. 2026. arXiv:2603.18043 | Yes | **Yes.** "routing by self-claimed quality scores performs worse than random selection (simulated: 0.55 vs. 0.68; real models: 8.90 vs. 9.30)." The plan's limits are also accurate: no negotiation, 10 simulated delegates. |

Overall: all 14 numbered or named items exist, and both unnamed claims map to real papers. Fixes needed:
1. Xia et al.: drop or verify "adversarial susceptibility".
2. 2512.09254: soften "stronger models extract higher payoffs from weaker counterparts".
3. 2512.13063: note that it reports negotiation ability does *not* improve with better models.
4. 2603.20281: model-size heterogeneity stabilizes collusion rather than disrupting it.
5. Antitrust paper: cite through OpenReview (no arXiv ID found) and confirm authors.

## 2. Missing related work (verified on arXiv)

1. **arXiv:2606.09863**. "From Confident Closing to Silent Failure: Characterizing False Success in LLM Agents." Laksh Advani. 2026 (FAGEN@ICML2026). Relevance: agents report task completion when environment state shows otherwise. False success accounts for 45–48% of failures in tau2-bench single-control domains, and LLM judges reach AUROC ≤ 0.65 at detecting it. This is the closest prior work on the agent-to-principal report channel.
2. **arXiv:2512.04864**. "Are Your Agents Upward Deceivers?" Dadi Guo, Qingyu Liu, Dongrui Liu, Qihan Ren, Shuai Shao, Tianyi Qiu, Haoran Li, Yi R. Fung, Zhongjie Ba, Juntao Dai, Jiaming Ji, Zhikai Chen, Jialing Tao, Yaodong Yang, Jing Shao, Xia Hu. 2025. Relevance: defines "agentic upward deception", where agents hide failures from their user or superior. Includes a 200-task benchmark. Directly undercuts "the agent-to-principal channel is largely unexamined."
3. **arXiv:2602.06948**. "Agentic Uncertainty Reveals Agentic Overconfidence." Jean Kaddour, Srijan Patel, Gbètondji Dovonon, Leo Richter, Pasquale Minervini, Matt J. Kusner. 2026. Relevance: agents' self-assessed success is badly miscalibrated ("agents that succeed only 22% of the time predict 77% success"). This is overclaiming in self-reports.
4. **arXiv:2606.30383**. "Whose Side Is Your Agent On? Multi-Party Principal Loyalty in LLM Agents." Bojie Li, Noah Shi. 2026. Relevance: the agent acts for a principal (who "receives results") while negotiating with a counterparty. PrincipalBench tests leaks of principal constraints such as a minimum price. Very close to this setup.
5. **arXiv:2506.00073**. "The Automated but Risky Game: Modeling and Benchmarking Agent-to-Agent Negotiations and Transactions in Consumer Markets." Shenzhe Zhu, Jiao Sun, Yi Nian, Tobin South, Alex Pentland, Jiaxin Pei. 2025. Relevance: delegated consumer and merchant negotiation agents. Different agents get significantly different outcomes for users, and agents overspend or accept unreasonable deals.
6. **arXiv:2510.25779**. "Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets." Gagan Bansal, Wenyue Hua, Zezhou Huang, et al. (24 authors, Microsoft Research). 2025. Relevance: Assistant agents represent consumers in two-sided markets, with measures of user welfare, first-proposal bias and manipulation vulnerability.
7. **arXiv:2501.07913**. "Governing AI Agents." Noam Kolt. 2025 (Notre Dame Law Review, Vol. 101, forthcoming). Relevance: applies principal-agent theory and agency law to AI agents (information asymmetry, discretion, loyalty). Argues that monitoring and incentive design may fail. Theoretical framing for the principal-supervision gap.
8. **arXiv:2601.23211**. "Multi-Agent Systems Should be Treated as Principal-Agent Problems." Paulius Rauba, Simonas Cepenas, Mihaela van der Schaar. 2026. Relevance: argues that "agents report truthfully to the principal when incentives are fully aligned" but this breaks down when incentives diverge, causing "agency loss". Applies to human-to-LLM and LLM-to-LLM settings.

Also found but not in the top 8:
- arXiv:2602.22303, "Training Agents to Self-Report Misbehavior" (Lee, Chen, Korbak, 2026). Self-incrimination training for agents.
- arXiv:2608.18078, "Position: Collusion Risks Among AI Reasoning Agents Justify Certification Requirements..." (Riemer et al., ICML 2026). Shows CoT can be steered collusive in ways "not semantically detectable" by an LLM monitor, which is relevant to the CoT-faithfulness caveat.
- arXiv:2401.13138, "Visibility into AI Agents" (Chan et al., FAccT 2024). Covers monitoring and activity logging of agents.

## 3. BibTeX

```bibtex
@article{fish2024algorithmic,
  title={Algorithmic Collusion by Large Language Models},
  author={Fish, Sara and Gonczarowski, Yannai A. and Shorrer, Ran I.},
  journal={arXiv preprint arXiv:2404.00806},
  year={2024},
  note={Accepted to EC 2026}
}

@article{lin2024strategic,
  title={Strategic Collusion of {LLM} Agents: Market Division in Multi-Commodity Competitions},
  author={Lin, Ryan Y. and Ojha, Siddhartha and Cai, Kevin and Chen, Maxwell F.},
  journal={arXiv preprint arXiv:2410.00031},
  year={2024}
}

@article{tian2026prompt,
  title={Prompt Optimization Enables Stable Algorithmic Collusion in {LLM} Agents},
  author={Tian, Yingtao},
  journal={arXiv preprint arXiv:2604.17774},
  year={2026}
}

@article{bracalesyrnikov2026institutional,
  title={Institutional {AI}: Governing {LLM} Collusion in Multi-Agent {Cournot} Markets via Public Governance Graphs},
  author={Bracale Syrnikov, Marcantonio and Pierucci, Federico and Galisai, Marcello and Prandi, Matteo and Bisconti, Piercosma and Giarrusso, Francesco and Sorokoletova, Olga and Suriani, Vincenzo and Nardi, Daniele},
  journal={arXiv preprint arXiv:2601.11369},
  year={2026}
}

@article{keppo2026fragility,
  title={On the Fragility of {AI} Agent Collusion},
  author={Keppo, Jussi and Li, Yuze and Tsoukalas, Gerry and Yuan, Nuo},
  journal={arXiv preprint arXiv:2603.20281},
  year={2026}
}

@inproceedings{anto2026oversight,
  title={Oversight is Not Compliance: Tacit Collusion in {LLM} Pricing Agents Under Antitrust Regulation},
  author={Anto, Meiri and Vazquez, Juan J.},
  booktitle={International Conference on Machine Learning (ICML)},
  year={2026},
  url={https://openreview.net/forum?id=aPnAkoXjF2},
  note={Metadata from third-party index; verify on OpenReview}
}

@article{agrawal2025evaluating,
  title={Evaluating {LLM} Agent Collusion in Double Auctions},
  author={Agrawal, Kushal and Teo, Verona and Vazquez, Juan J. and Kunnavakkam, Sudarsh and Srikanth, Vishak and Liu, Andy},
  journal={arXiv preprint arXiv:2507.01413},
  year={2025},
  note={ICML 2025 Workshop on Multi-Agent Systems in the Era of Foundation Models}
}

@article{bianchi2024negotiationarena,
  title={How Well Can {LLMs} Negotiate? {NegotiationArena} Platform and Analysis},
  author={Bianchi, Federico and Chia, Patrick John and Yuksekgonul, Mert and Tagliabue, Jacopo and Jurafsky, Dan and Zou, James},
  journal={arXiv preprint arXiv:2402.05863},
  year={2024}
}

@inproceedings{davidson2024evaluating,
  title={Evaluating Language Model Agency through Negotiations},
  author={Davidson, Tim R. and Veselovsky, Veniamin and Josifoski, Martin and Peyrard, Maxime and Bosselut, Antoine and Kosinski, Michal and West, Robert},
  booktitle={International Conference on Learning Representations (ICLR)},
  year={2024},
  eprint={2401.04536},
  archivePrefix={arXiv}
}

@inproceedings{xia2024measuring,
  title={Measuring Bargaining Abilities of {LLMs}: A Benchmark and A Buyer-Enhancement Method},
  author={Xia, Tian and He, Zhiwei and Ren, Tong and Miao, Yibo and Zhang, Zhuosheng and Yang, Yang and Wang, Rui},
  booktitle={Findings of the Association for Computational Linguistics: ACL 2024},
  year={2024},
  eprint={2402.15813},
  archivePrefix={arXiv}
}

@article{abdelnabi2023cooperation,
  title={Cooperation, Competition, and Maliciousness: {LLM}-Stakeholders Interactive Negotiation},
  author={Abdelnabi, Sahar and Gomaa, Amr and Sivaprasad, Sarath and Sch{\"o}nherr, Lea and Fritz, Mario},
  journal={arXiv preprint arXiv:2309.17234},
  year={2023}
}

@article{rios2025illusion,
  title={The Illusion of Rationality: Tacit Bias and Strategic Dominance in Frontier {LLM} Negotiation Games},
  author={R{\'i}os, Manuel S. and Manrique, Ruben F. and Quijano, Nicanor and Giraldo, Luis F.},
  journal={arXiv preprint arXiv:2512.09254},
  year={2025}
}

@article{liu2026agenticpay,
  title={{AgenticPay}: A Multi-Agent {LLM} Negotiation System for Buyer-Seller Transactions},
  author={Liu, Xianyang and Gu, Shangding and Song, Dawn},
  journal={arXiv preprint arXiv:2602.06008},
  year={2026}
}

@article{shah2025llmrationalis,
  title={{LLM} Rationalis? Measuring Bargaining Capabilities of {AI} Negotiators},
  author={Shah, Cheril and Agarwal, Akshit and Garg, Kanak and Heddaya, Mourad},
  journal={arXiv preprint arXiv:2512.13063},
  year={2025},
  note={NeurIPS 2025 Workshop on Multi-Turn Interactions in Large Language Models}
}

@article{coffey2026thinking,
  title={Thinking Out Loud: Real-Time Deception Monitoring in Asymmetric {LLM} Negotiations},
  author={Coffey, Nolan and Odoi, Faithful and Johnson, Makenzie and Eisty, Nasir U.},
  journal={arXiv preprint arXiv:2606.30649},
  year={2026}
}

@article{prakash2026provenance,
  title={The Provenance Paradox in Multi-Agent {LLM} Routing: Delegation Contracts and Attested Identity in {LDP}},
  author={Prakash, Sunil},
  journal={arXiv preprint arXiv:2603.18043},
  year={2026}
}

@article{advani2026falsesuccess,
  title={From Confident Closing to Silent Failure: Characterizing False Success in {LLM} Agents},
  author={Advani, Laksh},
  journal={arXiv preprint arXiv:2606.09863},
  year={2026},
  note={FAGEN@ICML2026}
}

@article{guo2025upward,
  title={Are Your Agents Upward Deceivers?},
  author={Guo, Dadi and Liu, Qingyu and Liu, Dongrui and Ren, Qihan and Shao, Shuai and Qiu, Tianyi and Li, Haoran and Fung, Yi R. and Ba, Zhongjie and Dai, Juntao and Ji, Jiaming and Chen, Zhikai and Tao, Jialing and Yang, Yaodong and Shao, Jing and Hu, Xia},
  journal={arXiv preprint arXiv:2512.04864},
  year={2025}
}

@article{kaddour2026agentic,
  title={Agentic Uncertainty Reveals Agentic Overconfidence},
  author={Kaddour, Jean and Patel, Srijan and Dovonon, Gb{\`e}tondji and Richter, Leo and Minervini, Pasquale and Kusner, Matt J.},
  journal={arXiv preprint arXiv:2602.06948},
  year={2026}
}

@article{li2026whoseside,
  title={Whose Side Is Your Agent On? Multi-Party Principal Loyalty in {LLM} Agents},
  author={Li, Bojie and Shi, Noah},
  journal={arXiv preprint arXiv:2606.30383},
  year={2026}
}

@article{zhu2025automated,
  title={The Automated but Risky Game: Modeling and Benchmarking Agent-to-Agent Negotiations and Transactions in Consumer Markets},
  author={Zhu, Shenzhe and Sun, Jiao and Nian, Yi and South, Tobin and Pentland, Alex and Pei, Jiaxin},
  journal={arXiv preprint arXiv:2506.00073},
  year={2025}
}

@article{bansal2025magentic,
  title={Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets},
  author={Bansal, Gagan and Hua, Wenyue and Huang, Zezhou and Fourney, Adam and Swearngin, Amanda and Epperson, Will and Payne, Tyler and Hofman, Jake M. and Lucier, Brendan and Singh, Chinmay and Mobius, Markus and Nambi, Akshay and Yadav, Archana and Gao, Kevin and Rothschild, David M. and Slivkins, Aleksandrs and Goldstein, Daniel G. and Mozannar, Hussein and Immorlica, Nicole and Murad, Maya and Vogel, Matthew and Kambhampati, Subbarao and Horvitz, Eric and Amershi, Saleema},
  journal={arXiv preprint arXiv:2510.25779},
  year={2025}
}

@article{kolt2025governing,
  title={Governing {AI} Agents},
  author={Kolt, Noam},
  journal={Notre Dame Law Review},
  volume={101},
  year={2025},
  note={Forthcoming; arXiv:2501.07913}
}

@article{rauba2026principalagent,
  title={Multi-Agent Systems Should be Treated as Principal-Agent Problems},
  author={Rauba, Paulius and Cepenas, Simonas and van der Schaar, Mihaela},
  journal={arXiv preprint arXiv:2601.23211},
  year={2026}
}

@article{lee2026selfreport,
  title={Training Agents to Self-Report Misbehavior},
  author={Lee, Bruce W. and Chen, Yueh-Han and Korbak, Tomek},
  journal={arXiv preprint arXiv:2602.22303},
  year={2026}
}

@inproceedings{riemer2026collusion,
  title={Position: Collusion Risks Among {AI} Reasoning Agents Justify Certification Requirements for Making Market Decisions},
  author={Riemer, Matthew and Tosato, Tommaso and Memarian, Amin and Puelma Touzel, Maximilian and Berseth, Glen and Rish, Irina and Dumas, Guillaume},
  booktitle={International Conference on Machine Learning (ICML)},
  year={2026},
  eprint={2608.18078},
  archivePrefix={arXiv}
}

@inproceedings{chan2024visibility,
  title={Visibility into {AI} Agents},
  author={Chan, Alan and Ezell, Carson and Kaufmann, Max and Wei, Kevin and Hammond, Lewis and Bradley, Herbie and Bluemke, Emma and Rajkumar, Nitarshan and Krueger, David and Kolt, Noam and Heim, Lennart and Anderljung, Markus},
  booktitle={ACM Conference on Fairness, Accountability, and Transparency (FAccT)},
  year={2024},
  eprint={2401.13138},
  archivePrefix={arXiv}
}
```
