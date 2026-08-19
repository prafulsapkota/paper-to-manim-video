from manimlib import *


class ExplainerVideo(Scene):
    """
    Comprehensive animated explainer video for the research paper:
    'TradingAgents: Multi-Agents LLM Financial Trading Framework'
    by Yijia Xiao, Edward Sun, Di Luo, Wei Wang (UCLA, MIT, Tauric Research).
    """

    def construct(self):
        """Execute all scenes in sequential order."""
        self.scene_01_title_card()
        self.scene_02_motivation_and_limitations()
        self.scene_03_analyst_team()
        self.scene_04_researcher_debate()
        self.scene_05_trader_and_risk_management()
        self.scene_06_communication_and_backbone()
        self.scene_07_experimental_results()
        self.scene_08_key_takeaways()

    def scene_01_title_card(self):
        """Title card displaying paper title, authors, affiliations, and core theme."""
        banner_box = RoundedRectangle(
            width=6.0,
            height=0.65,
            corner_radius=0.12,
            color=BLUE_D,
            fill_color=BLUE_E,
            fill_opacity=0.6,
        )
        banner_text = Text(
            "Tauric Research  ·  UCLA  ·  MIT",
            font_size=19,
            color=BLUE_A,
        ).move_to(banner_box)
        top_banner = VGroup(banner_box, banner_text).to_edge(UP, buff=0.7)

        title = Text(
            "TradingAgents: Multi-Agents LLM\nFinancial Trading Framework",
            font_size=42,
            color=WHITE,
            alignment="center",
        )
        title.next_to(top_banner, DOWN, buff=0.4)

        underline = Line(LEFT * 5.2, RIGHT * 5.2, color=TEAL_C, stroke_width=3)
        underline.next_to(title, DOWN, buff=0.3)

        authors = Text(
            "Yijia Xiao   ·   Edward Sun   ·   Di Luo   ·   Wei Wang",
            font_size=22,
            color=GREY_A,
        )
        authors.next_to(underline, DOWN, buff=0.35)

        tagline = Text(
            "Replicating Professional Trading Firm Dynamics with Collaborative LLM Societies",
            font_size=20,
            color=GOLD_C,
        )
        tagline.next_to(authors, DOWN, buff=0.45)

        self.play(FadeIn(top_banner, shift=DOWN * 0.2), run_time=0.8)
        self.play(Write(title), run_time=1.8)
        self.play(ShowCreation(underline), FadeIn(authors, shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(tagline, shift=UP * 0.2), run_time=1.0)
        self.wait(3.5)
        self.play(
            FadeOut(
                VGroup(top_banner, title, underline, authors, tagline),
                shift=UP * 0.4,
            ),
            run_time=0.8,
        )

    def scene_02_motivation_and_limitations(self):
        """Explain the limitations of existing approaches and the TradingAgents paradigm."""
        heading = Text("The Challenge in AI Financial Trading", font_size=36, color=BLUE_C)
        heading.to_edge(UP, buff=0.5)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(heading, DOWN, buff=0.2)

        box_left = RoundedRectangle(
            width=5.8,
            height=4.8,
            corner_radius=0.2,
            color=RED_C,
            fill_color=RED_E,
            fill_opacity=0.2,
        )
        box_left.move_to(LEFT * 3.3 + DOWN * 0.45)

        title_left = Text("Prior Limitations", font_size=23, color=RED_C)
        title_left.next_to(box_left.get_top(), DOWN, buff=0.25)

        p1_title = Text("1. Lack of Realistic Firm Structure", font_size=18, color=WHITE)
        p1_desc = Text("   • Isolated agents without human-like division of labor", font_size=15, color=GREY_A)
        p2_title = Text("2. Inefficient Natural Language Chat", font_size=18, color=WHITE)
        p2_desc = Text("   • 'Telephone game' distortion & context explosion", font_size=15, color=GREY_A)
        p3_title = Text("3. Black-Box Quantitative Models", font_size=18, color=WHITE)
        p3_desc = Text("   • Lack explainable rationale & multi-modal signals", font_size=15, color=GREY_A)

        points_left = VGroup(p1_title, p1_desc, p2_title, p2_desc, p3_title, p3_desc)
        points_left.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        points_left.next_to(title_left, DOWN, buff=0.22)
        points_left.align_to(box_left, LEFT).shift(RIGHT * 0.25)

        left_group = VGroup(box_left, title_left, points_left)

        box_right = RoundedRectangle(
            width=5.8,
            height=4.8,
            corner_radius=0.2,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.2,
        )
        box_right.move_to(RIGHT * 3.3 + DOWN * 0.45)

        title_right = Text("TradingAgents Solution", font_size=23, color=GREEN_C)
        title_right.next_to(box_right.get_top(), DOWN, buff=0.25)

        pr1_title = Text("1. Specialized Firm Hierarchy", font_size=18, color=WHITE)
        pr1_desc = Text("   • Analysts, Debating Researchers, Risk Team, Trader", font_size=15, color=GREY_A)
        pr2_title = Text("2. Structured Communication Protocol", font_size=18, color=WHITE)
        pr2_desc = Text("   • Modular state reports eliminate message corruption", font_size=15, color=GREY_A)
        pr3_title = Text("3. Dialectical Debates & 3-Tier Risk", font_size=18, color=WHITE)
        pr3_desc = Text("   • Bull vs Bear debate + multi-profile risk control", font_size=15, color=GREY_A)

        points_right = VGroup(pr1_title, pr1_desc, pr2_title, pr2_desc, pr3_title, pr3_desc)
        points_right.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        points_right.next_to(title_right, DOWN, buff=0.22)
        points_right.align_to(box_right, LEFT).shift(RIGHT * 0.25)

        right_group = VGroup(box_right, title_right, points_right)

        self.play(FadeIn(heading), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(left_group, shift=RIGHT * 0.3), run_time=1.2)
        self.wait(1.5)
        self.play(FadeIn(right_group, shift=LEFT * 0.3), run_time=1.2)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(heading, sep, left_group, right_group),
                shift=DOWN * 0.3,
            ),
            run_time=0.8,
        )

    def scene_03_analyst_team(self):
        """Present the 4 specialized market analyst agents and their data streams."""
        heading = Text("Phase 1: Specialized Analyst Team", font_size=36, color=BLUE_C)
        heading.to_edge(UP, buff=0.5)
        sub = Text(
            "Gathering multi-modal financial data and synthesizing structured reports",
            font_size=19,
            color=GREY_A,
        )
        sub.next_to(heading, DOWN, buff=0.15)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(sub, DOWN, buff=0.2)

        def make_analyst_card(title_text, color, points, position):
            """Construct a styled visual card representing an analyst role."""
            card = RoundedRectangle(
                width=5.6,
                height=2.0,
                corner_radius=0.15,
                color=color,
                fill_color=color,
                fill_opacity=0.15,
            )
            card.move_to(position)
            t = Text(title_text, font_size=19, color=color)
            t.next_to(card.get_top(), DOWN, buff=0.18)

            body = VGroup(*[Text(f"• {p}", font_size=14, color=WHITE) for p in points])
            body.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            body.next_to(t, DOWN, buff=0.12)
            body.align_to(card, LEFT).shift(RIGHT * 0.25)
            return VGroup(card, t, body)

        card1 = make_analyst_card(
            "Fundamentals Analyst",
            TEAL_C,
            [
                "Company financials & quarterly 10-Q / 10-K filings",
                "Profitability (ROE, ROA, Margins) & Solvency",
                "Valuation metrics (P/E, P/B) & Insider transactions",
            ],
            LEFT * 3.4 + UP * 0.7,
        )

        card2 = make_analyst_card(
            "Sentiment Analyst",
            GOLD_C,
            [
                "Social media tracking (Reddit WallStreetBets, X/Twitter)",
                "Retail sentiment spikes & community discussion peaks",
                "Auxiliary sentiment NLP scoring models",
            ],
            RIGHT * 3.4 + UP * 0.7,
        )

        card3 = make_analyst_card(
            "News Analyst",
            BLUE_B,
            [
                "Macroeconomic policies & Federal Reserve rate decisions",
                "Geopolitical risks & US-China trade dynamics",
                "Breaking sector & competitor industry developments",
            ],
            LEFT * 3.4 + DOWN * 1.8,
        )

        card4 = make_analyst_card(
            "Technical Analyst",
            GREEN_C,
            [
                "60+ quantitative technical indicators per asset",
                "Momentum & Trend: RSI, MACD, ADX, Supertrend",
                "Volatility & Volume: Bollinger Bands, ATR, VWMA, CCI",
            ],
            RIGHT * 3.4 + DOWN * 1.8,
        )

        center_hub = RoundedRectangle(
            width=2.8,
            height=0.8,
            corner_radius=0.1,
            color=WHITE,
            fill_color=GREY_E,
            fill_opacity=0.8,
        ).move_to(DOWN * 0.55)
        hub_text = Text("Global State Storage", font_size=14, color=GOLD_C).move_to(center_hub)
        hub_group = VGroup(center_hub, hub_text)

        arrow_c1 = Arrow(card1.get_bottom(), center_hub.get_top(), color=TEAL_C, stroke_width=2, buff=0.1)
        arrow_c2 = Arrow(card2.get_bottom(), center_hub.get_top(), color=GOLD_C, stroke_width=2, buff=0.1)
        arrow_c3 = Arrow(card3.get_top(), center_hub.get_bottom(), color=BLUE_B, stroke_width=2, buff=0.1)
        arrow_c4 = Arrow(card4.get_top(), center_hub.get_bottom(), color=GREEN_C, stroke_width=2, buff=0.1)
        arrows_hub = VGroup(arrow_c1, arrow_c2, arrow_c3, arrow_c4)

        self.play(FadeIn(heading), FadeIn(sub), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(card1, shift=DOWN * 0.2), FadeIn(card2, shift=DOWN * 0.2), run_time=1.0)
        self.play(FadeIn(card3, shift=UP * 0.2), FadeIn(card4, shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(hub_group), ShowCreation(arrows_hub), run_time=1.0)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(heading, sub, sep, card1, card2, card3, card4, hub_group, arrows_hub),
                shift=UP * 0.3,
            ),
            run_time=0.8,
        )

    def scene_04_researcher_debate(self):
        """Show the dialectical Bull vs Bear multi-round debate mechanism."""
        heading = Text("Phase 2: Dialectical Bull vs Bear Debate", font_size=36, color=GOLD_C)
        heading.to_edge(UP, buff=0.5)
        sub = Text(
            "Opposing researcher agents critically stress-test the analyst findings",
            font_size=19,
            color=GREY_A,
        )
        sub.next_to(heading, DOWN, buff=0.15)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(sub, DOWN, buff=0.2)

        bull_box = RoundedRectangle(
            width=5.3,
            height=3.4,
            corner_radius=0.2,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.25,
        ).move_to(LEFT * 3.4 + UP * 0.2)

        bull_title = Text("Bullish Researcher", font_size=21, color=GREEN_C)
        bull_title.next_to(bull_box.get_top(), DOWN, buff=0.22)
        bull_points = VGroup(
            Text("• Growth potential & AI ecosystem", font_size=15, color=WHITE),
            Text("• High profit margins (46% gross)", font_size=15, color=WHITE),
            Text("• Strong institutional accumulation", font_size=15, color=WHITE),
            Text("• Technical bullish breakout signals", font_size=15, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        bull_points.next_to(bull_title, DOWN, buff=0.22)
        bull_group = VGroup(bull_box, bull_title, bull_points)

        bear_box = RoundedRectangle(
            width=5.3,
            height=3.4,
            corner_radius=0.2,
            color=RED_C,
            fill_color=RED_E,
            fill_opacity=0.25,
        ).move_to(RIGHT * 3.4 + UP * 0.2)

        bear_title = Text("Bearish Researcher", font_size=21, color=RED_C)
        bear_title.next_to(bear_box.get_top(), DOWN, buff=0.22)
        bear_points = VGroup(
            Text("• Stretched valuation (P/E ~38x)", font_size=15, color=WHITE),
            Text("• Geopolitical supply chain exposure", font_size=15, color=WHITE),
            Text("• Insider selling & liquidity ratios < 1", font_size=15, color=WHITE),
            Text("• Overbought RSI & potential pullbacks", font_size=15, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        bear_points.next_to(bear_title, DOWN, buff=0.22)
        bear_group = VGroup(bear_box, bear_title, bear_points)

        vs_circle = Circle(radius=0.55, color=GOLD_C, fill_color=BLACK, fill_opacity=0.9)
        vs_circle.move_to(UP * 0.2)
        vs_text = Text("VS", font_size=22, color=GOLD_C).move_to(vs_circle)
        vs_group = VGroup(vs_circle, vs_text)

        debate_arrow_r = Arrow(
            bull_box.get_right() + UP * 0.5,
            bear_box.get_left() + UP * 0.5,
            color=GREEN_C,
            buff=0.75,
            stroke_width=2.5,
        )
        debate_arrow_l = Arrow(
            bear_box.get_left() + DOWN * 0.5,
            bull_box.get_right() + DOWN * 0.5,
            color=RED_C,
            buff=0.75,
            stroke_width=2.5,
        )

        moderator_box = RoundedRectangle(
            width=11.2,
            height=1.2,
            corner_radius=0.15,
            color=BLUE_C,
            fill_color=BLUE_E,
            fill_opacity=0.4,
        ).move_to(DOWN * 2.5)
        mod_title = Text("Debate Facilitator Agent", font_size=18, color=BLUE_B)
        mod_title.next_to(moderator_box.get_top(), DOWN, buff=0.15)
        mod_desc = Text(
            "Moderates N rounds of structured dialectical discourse → Synthesizes debiased market outlook",
            font_size=15,
            color=WHITE,
        )
        mod_desc.next_to(mod_title, DOWN, buff=0.12)
        moderator_group = VGroup(moderator_box, mod_title, mod_desc)

        self.play(FadeIn(heading), FadeIn(sub), ShowCreation(sep), run_time=0.8)
        self.play(
            FadeIn(bull_group, shift=RIGHT * 0.3),
            FadeIn(bear_group, shift=LEFT * 0.3),
            FadeIn(vs_group),
            run_time=1.2,
        )
        self.play(
            ShowCreation(debate_arrow_r),
            ShowCreation(debate_arrow_l),
            run_time=1.0,
        )
        self.play(FadeIn(moderator_group, shift=UP * 0.2), run_time=0.8)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(
                    heading,
                    sub,
                    sep,
                    bull_group,
                    bear_group,
                    vs_group,
                    debate_arrow_r,
                    debate_arrow_l,
                    moderator_group,
                ),
                shift=DOWN * 0.3,
            ),
            run_time=0.8,
        )

    def scene_05_trader_and_risk_management(self):
        """Illustrate Trader proposal, 3-tier Risk Management Council, and Fund Manager execution."""
        heading = Text("Phase 3: Trading & 3-Tier Risk Management", font_size=36, color=TEAL_C)
        heading.to_edge(UP, buff=0.5)
        sub = Text(
            "Formulating trade proposals and subjecting them to multi-perspective risk calibration",
            font_size=19,
            color=GREY_A,
        )
        sub.next_to(heading, DOWN, buff=0.15)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(sub, DOWN, buff=0.2)

        trader_card = RoundedRectangle(
            width=3.2,
            height=2.3,
            corner_radius=0.15,
            color=BLUE_C,
            fill_color=BLUE_E,
            fill_opacity=0.3,
        ).move_to(LEFT * 4.6 + UP * 0.2)
        trader_title = Text("Trader Agent", font_size=19, color=BLUE_C)
        trader_title.next_to(trader_card.get_top(), DOWN, buff=0.18)
        trader_desc = VGroup(
            Text("• Evaluates reports", font_size=14, color=WHITE),
            Text("• Sets order size", font_size=14, color=WHITE),
            Text("• Drafts rationale", font_size=14, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        trader_desc.next_to(trader_title, DOWN, buff=0.16)
        trader_group = VGroup(trader_card, trader_title, trader_desc)

        arrow_1 = Arrow(LEFT * 2.9 + UP * 0.2, LEFT * 1.9 + UP * 0.2, color=GREY_A, stroke_width=2.5)

        risk_container = RoundedRectangle(
            width=4.8,
            height=3.3,
            corner_radius=0.2,
            color=GOLD_C,
            fill_color=GOLD_E,
            fill_opacity=0.15,
        ).move_to(RIGHT * 0.6 + UP * 0.2)
        risk_header = Text("Risk Management Team (3 Profiles)", font_size=17, color=GOLD_C)
        risk_header.next_to(risk_container.get_top(), DOWN, buff=0.18)

        risk_r = RoundedRectangle(
            width=4.2,
            height=0.62,
            corner_radius=0.1,
            color=RED_C,
            fill_color=RED_E,
            fill_opacity=0.4,
        )
        risk_r_text = Text("Aggressive Analyst: Maximize upside momentum", font_size=13, color=WHITE).move_to(risk_r)
        tier_r = VGroup(risk_r, risk_r_text)

        risk_n = RoundedRectangle(
            width=4.2,
            height=0.62,
            corner_radius=0.1,
            color=BLUE_B,
            fill_color=BLUE_E,
            fill_opacity=0.4,
        )
        risk_n_text = Text("Neutral Analyst: Balance hedges & volatility", font_size=13, color=WHITE).move_to(risk_n)
        tier_n = VGroup(risk_n, risk_n_text)

        risk_c = RoundedRectangle(
            width=4.2,
            height=0.62,
            corner_radius=0.1,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.4,
        )
        risk_c_text = Text("Conservative Analyst: Protect capital & drawdowns", font_size=13, color=WHITE).move_to(risk_c)
        tier_c = VGroup(risk_c, risk_c_text)

        tiers = VGroup(tier_r, tier_n, tier_c).arrange(DOWN, buff=0.12)
        tiers.next_to(risk_header, DOWN, buff=0.16)
        risk_group = VGroup(risk_container, risk_header, tiers)

        arrow_2 = Arrow(RIGHT * 3.1 + UP * 0.2, RIGHT * 4.1 + UP * 0.2, color=GREY_A, stroke_width=2.5)

        fm_card = RoundedRectangle(
            width=2.8,
            height=2.3,
            corner_radius=0.15,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.3,
        ).move_to(RIGHT * 5.6 + UP * 0.2)
        fm_title = Text("Fund Manager", font_size=19, color=GREEN_C)
        fm_title.next_to(fm_card.get_top(), DOWN, buff=0.18)
        fm_desc = VGroup(
            Text("• Final review", font_size=14, color=WHITE),
            Text("• Risk adjustment", font_size=14, color=WHITE),
            Text("• Order execution", font_size=14, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        fm_desc.next_to(fm_title, DOWN, buff=0.16)
        fm_group = VGroup(fm_card, fm_title, fm_desc)

        bottom_badge = RoundedRectangle(
            width=11.5,
            height=0.8,
            corner_radius=0.15,
            color=TEAL_D,
            fill_color=TEAL_E,
            fill_opacity=0.4,
        ).move_to(DOWN * 2.5)
        bottom_text = Text(
            "Tri-factor risk evaluation ensures high return generation while strictly curbing max drawdown",
            font_size=15,
            color=WHITE,
        ).move_to(bottom_badge)
        bottom_group = VGroup(bottom_badge, bottom_text)

        self.play(FadeIn(heading), FadeIn(sub), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(trader_group, shift=RIGHT * 0.2), run_time=0.8)
        self.play(ShowCreation(arrow_1), FadeIn(risk_group, shift=UP * 0.2), run_time=1.0)
        self.play(ShowCreation(arrow_2), FadeIn(fm_group, shift=LEFT * 0.2), run_time=0.8)
        self.play(FadeIn(bottom_group, shift=UP * 0.2), run_time=0.8)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(
                    heading,
                    sub,
                    sep,
                    trader_group,
                    arrow_1,
                    risk_group,
                    arrow_2,
                    fm_group,
                    bottom_group,
                ),
                shift=DOWN * 0.3,
            ),
            run_time=0.8,
        )

    def scene_06_communication_and_backbone(self):
        """Explain the structured communication protocol and hybrid backbone LLM architecture."""
        heading = Text("System Design: Protocols & Hybrid LLM Models", font_size=36, color=BLUE_C)
        heading.to_edge(UP, buff=0.5)
        sub = Text(
            "Preventing context distortion and optimizing speed vs. deep reasoning capability",
            font_size=19,
            color=GREY_A,
        )
        sub.next_to(heading, DOWN, buff=0.15)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(sub, DOWN, buff=0.2)

        box_proto = RoundedRectangle(
            width=5.8,
            height=4.6,
            corner_radius=0.2,
            color=BLUE_B,
            fill_color=BLUE_E,
            fill_opacity=0.2,
        ).move_to(LEFT * 3.3 + DOWN * 0.45)
        proto_title = Text("Structured State Protocol", font_size=21, color=BLUE_B)
        proto_title.next_to(box_proto.get_top(), DOWN, buff=0.22)
        proto_points = VGroup(
            Text("• Global Agent State Storage", font_size=17, color=GOLD_C),
            Text("   Agents query only necessary data blocks", font_size=14, color=GREY_A),
            Text("• Structured Document Exchange", font_size=17, color=GOLD_C),
            Text("   Concise standardized analysis reports", font_size=14, color=GREY_A),
            Text("• Targeted Natural Language Dialogue", font_size=17, color=GOLD_C),
            Text("   Reserved strictly for debates & risk council", font_size=14, color=GREY_A),
            Text("• Zero 'Telephone Game' Drift", font_size=17, color=GREEN_C),
            Text("   Guarantees long-horizon message integrity", font_size=14, color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        proto_points.next_to(proto_title, DOWN, buff=0.18)
        proto_points.align_to(box_proto, LEFT).shift(RIGHT * 0.25)
        proto_group = VGroup(box_proto, proto_title, proto_points)

        box_models = RoundedRectangle(
            width=5.8,
            height=4.6,
            corner_radius=0.2,
            color=TEAL_C,
            fill_color=TEAL_E,
            fill_opacity=0.2,
        ).move_to(RIGHT * 3.3 + DOWN * 0.45)
        models_title = Text("Dual-Tier Backbone LLMs", font_size=21, color=TEAL_C)
        models_title.next_to(box_models.get_top(), DOWN, buff=0.22)

        card_deep = RoundedRectangle(
            width=5.0,
            height=1.7,
            corner_radius=0.15,
            color=PURPLE_C,
            fill_color=PURPLE_E,
            fill_opacity=0.3,
        )
        card_deep_title = Text("Deep-Thinking Models (e.g. o1-preview)", font_size=15, color=PURPLE_B)
        card_deep_title.next_to(card_deep.get_top(), DOWN, buff=0.15)
        card_deep_text = VGroup(
            Text("• Multi-round dialectical reasoning", font_size=13, color=WHITE),
            Text("• Complex risk evaluation & decision-making", font_size=13, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        card_deep_text.next_to(card_deep_title, DOWN, buff=0.1)
        deep_group = VGroup(card_deep, card_deep_title, card_deep_text)

        card_quick = RoundedRectangle(
            width=5.0,
            height=1.7,
            corner_radius=0.15,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.3,
        )
        card_quick_title = Text("Quick-Thinking Models (e.g. gpt-4o / mini)", font_size=15, color=GREEN_C)
        card_quick_title.next_to(card_quick.get_top(), DOWN, buff=0.15)
        card_quick_text = VGroup(
            Text("• High-throughput tool calling & API queries", font_size=13, color=WHITE),
            Text("• Fast tabular parsing & data summarization", font_size=13, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        card_quick_text.next_to(card_quick_title, DOWN, buff=0.1)
        quick_group = VGroup(card_quick, card_quick_title, card_quick_text)

        models_inner = VGroup(deep_group, quick_group).arrange(DOWN, buff=0.18)
        models_inner.next_to(models_title, DOWN, buff=0.18)
        models_group = VGroup(box_models, models_title, models_inner)

        self.play(FadeIn(heading), FadeIn(sub), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(proto_group, shift=RIGHT * 0.2), run_time=1.0)
        self.play(FadeIn(models_group, shift=LEFT * 0.2), run_time=1.0)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(heading, sub, sep, proto_group, models_group),
                shift=UP * 0.3,
            ),
            run_time=0.8,
        )

    def scene_07_experimental_results(self):
        """Show backtesting results comparing TradingAgents to rule-based & market baselines."""
        heading = Text("Backtesting Results (Q1 2024 Simulation)", font_size=36, color=GREEN_C)
        heading.to_edge(UP, buff=0.5)
        sub = Text(
            "Multi-asset evaluation (Apple, Google, Amazon) eliminating look-ahead bias",
            font_size=19,
            color=GREY_A,
        )
        sub.next_to(heading, DOWN, buff=0.15)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(sub, DOWN, buff=0.2)

        table_bg = RoundedRectangle(
            width=12.2,
            height=3.2,
            corner_radius=0.15,
            color=GREY_D,
            fill_color=BLACK,
            fill_opacity=0.6,
        ).move_to(UP * 0.5)

        headers = ["Stock / Asset", "Market B&H", "Best Rule Baseline", "TradingAgents", "Sharpe Ratio (SR)"]
        header_mobs = [Text(h, font_size=17, color=GOLD_C) for h in headers]

        row1 = ["AAPL (Apple)", "-5.23%", "+2.05% (KDJ+RSI)", "+26.62%", "8.21 (vs -1.29)"]
        row2 = ["GOOGL (Google)", "+7.78%", "+6.23% (SMA)", "+24.36%", "6.39 (vs 1.35)"]
        row3 = ["AMZN (Amazon)", "+17.10%", "+11.01% (SMA)", "+23.21%", "5.60 (vs 3.53)"]

        rows_data = [row1, row2, row3]
        all_cells = []
        all_cells.extend(header_mobs)

        for r in rows_data:
            for i, val in enumerate(r):
                if i == 0:
                    c = WHITE
                elif i == 3:
                    c = GREEN_C
                elif i == 4:
                    c = TEAL_C
                else:
                    c = GREY_A
                all_cells.append(Text(val, font_size=16, color=c))

        grid = VGroup(*all_cells)
        grid.arrange_in_grid(n_rows=4, n_cols=5, h_buff=0.55, v_buff=0.35)
        grid.move_to(table_bg.get_center())
        table_group = VGroup(table_bg, grid)

        callout1 = RoundedRectangle(
            width=3.7,
            height=1.5,
            corner_radius=0.15,
            color=GREEN_C,
            fill_color=GREEN_E,
            fill_opacity=0.3,
        )
        c1_t1 = Text("Cumulative Returns", font_size=15, color=GREEN_C)
        c1_t2 = Text("+23.2% to +26.6%", font_size=20, color=WHITE)
        c1_t3 = Text("Surpasses best baseline by 6.1-24.5%", font_size=12, color=GREY_A)
        c1_group = VGroup(c1_t1, c1_t2, c1_t3).arrange(DOWN, buff=0.08)
        c1_full = VGroup(callout1, c1_group.move_to(callout1))

        callout2 = RoundedRectangle(
            width=3.7,
            height=1.5,
            corner_radius=0.15,
            color=TEAL_C,
            fill_color=TEAL_E,
            fill_opacity=0.3,
        )
        c2_t1 = Text("Risk-Adjusted Alpha", font_size=15, color=TEAL_C)
        c2_t2 = Text("Sharpe: 5.60 - 8.21", font_size=20, color=WHITE)
        c2_t3 = Text("Exceptional risk/reward efficiency", font_size=12, color=GREY_A)
        c2_group = VGroup(c2_t1, c2_t2, c2_t3).arrange(DOWN, buff=0.08)
        c2_full = VGroup(callout2, c2_group.move_to(callout2))

        callout3 = RoundedRectangle(
            width=3.7,
            height=1.5,
            corner_radius=0.15,
            color=GOLD_C,
            fill_color=GOLD_E,
            fill_opacity=0.3,
        )
        c3_t1 = Text("Drawdown Control", font_size=15, color=GOLD_C)
        c3_t2 = Text("MDD < 2.11%", font_size=20, color=WHITE)
        c3_t3 = Text("Strict risk manager constraints", font_size=12, color=GREY_A)
        c3_group = VGroup(c3_t1, c3_t2, c3_t3).arrange(DOWN, buff=0.08)
        c3_full = VGroup(callout3, c3_group.move_to(callout3))

        callouts = VGroup(c1_full, c2_full, c3_full).arrange(RIGHT, buff=0.45)
        callouts.move_to(DOWN * 2.3)

        self.play(FadeIn(heading), FadeIn(sub), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(table_group, shift=DOWN * 0.2), run_time=1.2)
        self.play(FadeIn(callouts, shift=UP * 0.2), run_time=1.0)
        self.wait(4.5)
        self.play(
            FadeOut(
                VGroup(heading, sub, sep, table_group, callouts),
                shift=DOWN * 0.3,
            ),
            run_time=0.8,
        )

    def scene_08_key_takeaways(self):
        """Summarize key contributions, advantages, and repository link."""
        heading = Text("Key Takeaways & Contributions", font_size=36, color=GOLD_C)
        heading.to_edge(UP, buff=0.5)
        sep = Line(LEFT * 6.2, RIGHT * 6.2, color=GREY_D, stroke_width=1.5)
        sep.next_to(heading, DOWN, buff=0.2)

        box_summary = RoundedRectangle(
            width=11.5,
            height=3.6,
            corner_radius=0.2,
            color=BLUE_D,
            fill_color=BLUE_E,
            fill_opacity=0.2,
        ).move_to(UP * 0.1)

        points = VGroup(
            Text(
                "1. Realistic Firm Hierarchy: 7 specialized roles (4 Analysts, 2 Debaters, 3 Risk, Trader).",
                font_size=18,
                color=WHITE,
            ),
            Text(
                "2. Dialectical Debates & 3-Tier Risk: Eliminates cognitive bias, hallucination & overexposure.",
                font_size=18,
                color=WHITE,
            ),
            Text(
                "3. Structured Protocol & Hybrid LLMs: Prevents context decay while optimizing cost and speed.",
                font_size=18,
                color=WHITE,
            ),
            Text(
                "4. SOTA Financial Performance: Outperforms standard baselines in Cumulative Returns and Sharpe Ratio.",
                font_size=18,
                color=WHITE,
            ),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        points.move_to(box_summary.get_center())
        summary_group = VGroup(box_summary, points)

        github_box = RoundedRectangle(
            width=8.0,
            height=0.85,
            corner_radius=0.15,
            color=TEAL_C,
            fill_color=TEAL_E,
            fill_opacity=0.4,
        ).move_to(DOWN * 2.6)
        gh_text = Text(
            "Open Source: github.com/TauricResearch/TradingAgents",
            font_size=19,
            color=GOLD_C,
        ).move_to(github_box)
        gh_group = VGroup(github_box, gh_text)

        self.play(FadeIn(heading), ShowCreation(sep), run_time=0.8)
        self.play(FadeIn(summary_group, shift=UP * 0.2), run_time=1.2)
        self.play(FadeIn(gh_group, shift=UP * 0.2), run_time=0.8)
        self.wait(4.0)
        self.play(
            FadeOut(
                VGroup(heading, sep, summary_group, gh_group),
                shift=DOWN * 0.3,
            ),
            run_time=0.8,
        )
