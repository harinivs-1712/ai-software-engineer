import ast
import operator

from tools.base import BaseTool


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Perform basic mathematical calculations "
            "including addition, subtraction, multiplication, "
            "division, percentages, powers, and parentheses."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "A mathematical expression such as "
                        "'235 * 87' or '(20 + 10) / 5'."
                    ),
                }
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs):
        expression = kwargs.get("expression")

        # -------------------------
        # Input validation
        # -------------------------

        if not isinstance(expression, str):
            return {
                "success": False,
                "error": "Expression must be a string.",
            }

        expression = expression.strip()

        if not expression:
            return {
                "success": False,
                "error": "Expression cannot be empty.",
            }

        if len(expression) > 200:
            return {
                "success": False,
                "error": (
                    "Expression is too long. "
                    "Maximum length is 200 characters."
                ),
            }

        # -------------------------
        # Calculate
        # -------------------------

        try:
            result = self._evaluate(expression)

            return {
                "success": True,
                "expression": expression,
                "result": result,
            }

        except ZeroDivisionError:
            return {
                "success": False,
                "expression": expression,
                "error": "Division by zero is not allowed.",
            }

        except (ValueError, TypeError, SyntaxError):
            return {
                "success": False,
                "expression": expression,
                "error": "Invalid mathematical expression.",
            }

        except Exception:
            return {
                "success": False,
                "expression": expression,
                "error": "Unable to evaluate expression.",
            }

    def _evaluate(self, expression: str):
        tree = ast.parse(
            expression,
            mode="eval",
        )

        return self._evaluate_node(tree.body)

    def _evaluate_node(self, node):

        # Number
        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError("Invalid value.")

        # Unary + / -
        if isinstance(node, ast.UnaryOp):

            operand = self._evaluate_node(node.operand)

            if isinstance(node.op, ast.USub):
                return -operand

            if isinstance(node.op, ast.UAdd):
                return +operand

            raise ValueError("Invalid unary operator.")

        # Binary operators
        if isinstance(node, ast.BinOp):

            left = self._evaluate_node(node.left)
            right = self._evaluate_node(node.right)

            operations = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }

            operation = operations.get(
                type(node.op)
            )

            if operation is None:
                raise ValueError(
                    "Unsupported operator."
                )

            return operation(left, right)

        raise ValueError(
            "Unsupported expression."
        )