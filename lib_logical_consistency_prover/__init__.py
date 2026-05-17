"""lib-logical-consistency-prover — formal logical consistency verification.

Verifies that specification logic is consistent with code contracts using
Z3 SMT solving (Layer M) with optional LLM evaluation (Layer L).

Public API:
    prove(spec, code, config) -> EvaluationResult

Example:
    from lib_logical_consistency_prover import prove
    from lib_logical_consistency_prover.models import SpecContent, CodeContent

    result = prove(spec_content, code_content)
    print(result.verdict)  # "pass" | "fail" | "warning" | "fp_candidate"
"""

from lib_logical_consistency_prover.prover import prove

__all__ = ["prove"]
__version__ = "0.1.0"
