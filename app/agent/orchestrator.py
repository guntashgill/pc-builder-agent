import logging
from typing import Optional, Tuple

from app.agent.interpreter import Interpreter
from app.agent.planner import Planner
from app.agent.critic import Critic
from app.validation import validate_build
from app.models import Constraints, PCBuild, ValidationResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main agent controller that orchestrates the plan-validate-revise loop.
    
    This is the core of the agentic system:
    1. Interprets user input into constraints
    2. Plans a build
    3. Validates the build
    4. If validation fails, critiques and revises
    5. Repeats until valid or max iterations reached
    """

    def __init__(
        self,
        interpreter: Optional[Interpreter] = None,
        planner: Optional[Planner] = None,
        critic: Optional[Critic] = None,
        max_iterations: int = 5
    ):
        """
        Initialize orchestrator with agent components

        Args:
            interpreter: Constraint extraction agent
            planner: Build generation agent
            critic: Failure analysis agent
            max_iterations: Maximum revision attempts before giving up
        """
        self.interpreter = interpreter or Interpreter()
        self.planner = planner or Planner()
        self.critic = critic or Critic()
        self.max_iterations = max_iterations

        logger.info(f"Orchestrator initialized (max_iterations={max_iterations})")

    def build_from_user_input(
        self,
        user_input: str
    ) -> Tuple[PCBuild, Constraints, int]:
        """
        Complete pipeline: user input → validated PC build

        Args:
            user_input: Natural language description of desired PC

        Returns:
            Tuple of (validated_build, constraints, iteration_count)

        Raises:
            ValueError: If constraints extraction fails
            RuntimeError: If valid build cannot be generated within max iterations
        """
        logger.info("="*70)
        logger.info("Starting build generation from user input")
        logger.info("="*70)

        # Step 1: Extract constraints
        logger.info("STEP 1: Extracting constraints from user input")
        constraints = self.interpreter.extract_constraints(user_input)
        logger.info(f"✓ Constraints: budget=${constraints.budget_usd}, "
                   f"workloads={constraints.primary_workloads}")

        # Step 2-5: Plan-validate-revise loop
        build = self._plan_validate_loop(constraints)

        return build

    def _plan_validate_loop(self, constraints: Constraints) -> PCBuild:
        """
        Core agentic loop: plan → validate → critique → revise

        Args:
            constraints: User requirements

        Returns:
            Valid PCBuild

        Raises:
            RuntimeError: If max iterations exceeded without valid build
        """
        previous_build: Optional[PCBuild] = None
        feedback: Optional[str] = None
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n{'='*70}")
            logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            logger.info(f"{'='*70}")

            # Step 2: Generate (or revise) build
            if iteration == 1:
                logger.info("STEP 2: Generating initial build")
            else:
                logger.info(f"STEP 2: Revising build (attempt {iteration})")
                logger.info(f"Feedback from critic:\n{feedback}")

            build = self.planner.generate_build(
                constraints=constraints,
                previous_build=previous_build,
                feedback=feedback
            )

            logger.info(f"✓ Build generated: {build.cpu.model}, {build.gpu.model if build.gpu else 'No GPU'}")
            logger.info(f"  Cost: ${build.estimated_cost_usd}")

            # Step 3: Validate build
            logger.info("STEP 3: Validating build compatibility")
            validation_result = validate_build(build, constraints)

            if validation_result.is_valid:
                logger.info("="*70)
                logger.info(f"✅ BUILD VALID! (completed in {iteration} iterations)")
                logger.info("="*70)
                return build

            # Build failed validation
            logger.warning(f"❌ Build validation failed:")
            logger.warning(f"   Errors: {len(validation_result.errors)}")
            for error in validation_result.errors:
                logger.warning(f"     - {error.message}")

            if validation_result.warnings:
                logger.warning(f"   Warnings: {len(validation_result.warnings)}")
                for warning in validation_result.warnings:
                    logger.warning(f"     - {warning.message}")

            # Step 4: Analyze failure and generate revision instructions
            logger.info("STEP 4: Analyzing failure with critic")
            critique = self.critic.analyze_failure(
                build=build,
                constraints=constraints,
                validation_result=validation_result
            )

            # Format feedback for planner
            feedback = self.critic.format_feedback_for_planner(critique)

            logger.info("✓ Critique generated, preparing for revision")

            # Save build for next iteration
            previous_build = build

        # Max iterations exceeded
        logger.error(f"Failed to generate valid build after {self.max_iterations} iterations")
        raise RuntimeError(
            f"Could not generate valid build within {self.max_iterations} attempts. "
            f"Last errors: {[e.message for e in validation_result.errors]}"
        )

    def quick_validate(self, build: PCBuild, constraints: Constraints) -> ValidationResult:
        """
        Validate an existing build without running the full loop

        Args:
            build: PC build to validate
            constraints: Original constraints

        Returns:
            ValidationResult
        """
        return validate_build(build, constraints)
