"""Initialize Sample Data"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import FraudSample, NormalSample, KnowledgeBase


async def init_sample_data():
    """Initialize sample data (idempotent: skip if data already exists)"""
    from app.database.session import async_session_maker
    from sqlalchemy import select, func

    async with async_session_maker() as session:
        # Check if data already exists to avoid duplicate insertion
        count_result = await session.execute(select(func.count(FraudSample.id)))
        existing_count = count_result.scalar()
        if existing_count > 0:
            print(f"Sample data already exists ({existing_count} entries), skipping initialization")
            return
        # Add fraud samples
        fraud_samples = [
            FraudSample(
                sample_type="url",
                content="http://fake-bank-login.com",
                fraud_category="Phishing Website",
                description="Fake bank login page",
                threat_level="high",
                source="System built-in"
            ),
            FraudSample(
                sample_type="sms",
                content="[Bank Notice] Your account has abnormal activity, please click the link immediately to verify: http://fake-verify.com",
                fraud_category="Bank Impersonation",
                description="Fake SMS impersonating a bank",
                threat_level="high",
                source="System built-in"
            ),
            FraudSample(
                sample_type="call",
                content="Hello, I am from the Public Security Bureau. You are involved in a money laundering case and need to cooperate with the investigation. Please transfer your funds to a safe account.",
                fraud_category="Impersonating Law Enforcement",
                description="Fraud call impersonating law enforcement",
                threat_level="critical",
                source="System built-in"
            ),
        ]

        # Add normal samples
        normal_samples = [
            NormalSample(
                sample_type="url",
                content="https://www.icbc.com.cn",
                category="Bank Official Website",
                description="ICBC (Industrial and Commercial Bank of China) official website",
                source="System built-in"
            ),
            NormalSample(
                sample_type="sms",
                content="[Bank] Your account balance is 10000.00 CNY",
                category="Bank Notification",
                description="Normal bank balance notification",
                source="System built-in"
            ),
        ]

        # Add knowledge base data
        knowledge_items = [
            KnowledgeBase(
                title="Common Telecom Fraud Tactics - Impersonating Law Enforcement",
                content="""
                Impersonating law enforcement is one of the most common fraud tactics. Scammers typically:
                1. Claim to be from the Public Security Bureau, Procuratorate, or Court
                2. Claim the victim is involved in a crime (money laundering, drug trafficking, etc.)
                3. Demand the victim transfer funds to a "safe account" for verification
                4. Use intimidation and threats to impair the victim's judgment

                Prevention tips:
                - Law enforcement agencies do not handle cases over the phone
                - There is no such thing as a "safe account"
                - They will never ask for a transfer or verification code
                - Hang up immediately and call the police if you receive such a call
                """,
                category="fraud_case",
                tags=["Law Enforcement", "Impersonation", "Safe Account"],
                source="System built-in"
            ),
            KnowledgeBase(
                title="How to Identify Phishing Websites",
                content="""
                Common characteristics of phishing websites:
                1. URL is similar to a legitimate website but with slight differences
                2. Uses HTTP instead of HTTPS
                3. Asks for sensitive information (passwords, verification codes, etc.)
                4. Poor page design or contains spelling errors
                5. Accessed through links in SMS or email

                Prevention suggestions:
                - Type the URL directly to visit the official website
                - Check if the URL is correct
                - Do not click on unknown links
                - Install security software for protection
                """,
                category="prevention_guide",
                tags=["Phishing Website", "Identification", "Prevention"],
                source="System built-in"
            ),
            KnowledgeBase(
                title="AI Voice Fraud Recognition Guide",
                content="""
                With the development of AI technology, voice fraud is becoming more common:

                Common methods:
                1. Using AI to synthesize a family member's voice asking for help
                2. Forging a boss's or friend's voice to borrow money
                3. Impersonating customer service personnel to commit fraud

                Recognition methods:
                - Ask the other person to say specific words or answer personal questions
                - Verify identity through other channels
                - Notice if the voice sounds mechanical or unnatural
                - Be wary of urgent help calls

                Countermeasures:
                - Do not trust identity claims made over the phone
                - Hang up and verify through other means of contact
                - Always verify through multiple channels when money transfers are involved
                - Report to the police promptly
                """,
                category="prevention_guide",
                tags=["AI Voice", "Voice Forgery", "Recognition"],
                source="System built-in"
            ),
        ]

        # Batch insert
        session.add_all(fraud_samples)
        session.add_all(normal_samples)
        session.add_all(knowledge_items)
        await session.commit()

        print(f"Added {len(fraud_samples)} fraud samples")
        print(f"Added {len(normal_samples)} normal samples")
        print(f"Added {len(knowledge_items)} knowledge base entries")
