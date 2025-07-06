# src/services/pricing_service.py
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple
from src.models.category import PriceRule, SpecificationTemplate
import logging

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_price(
        self, 
        subcategory_id: int, 
        specifications: Dict[str, Any], 
        base_price: int = None
    ) -> Tuple[int, List[Dict[str, Any]], Dict[str, int]]:
        """
        Calculate the final price based on specifications and pricing rules
        
        Returns:
            - final_price: int (in cents)
            - applied_rules: List of applied rules
            - price_breakdown: Dict showing price components
        """
        
        # Get all active price rules for this subcategory
        price_rules = self.db.query(PriceRule).filter(
            PriceRule.subcategory_id == subcategory_id,
            PriceRule.is_active == True
        ).order_by(PriceRule.rule_id).all()
        
        if not price_rules:
            logger.warning(f"No price rules found for subcategory {subcategory_id}")
            return base_price or 0, [], {"base_price": base_price or 0}
        
        # Find the best matching rule
        best_rule = None
        best_match_score = -1
        
        for rule in price_rules:
            match_score = self._calculate_match_score(rule.spec_conditions, specifications)
            if match_score > best_match_score:
                best_match_score = match_score
                best_rule = rule
        
        if not best_rule:
            logger.warning(f"No matching price rule found for specs: {specifications}")
            return base_price or 0, [], {"base_price": base_price or 0}
        
        # Calculate final price using the best rule
        final_price = self._apply_price_rule(best_rule, base_price)
        
        # Prepare response data
        applied_rules = [{
            "rule_id": best_rule.rule_id,
            "conditions": best_rule.spec_conditions,
            "base_price": best_rule.base_price,
            "modifier": best_rule.price_modifier,
            "modifier_type": best_rule.modifier_type,
            "match_score": best_match_score
        }]
        
        price_breakdown = {
            "base_price": best_rule.base_price,
            "modifier": best_rule.price_modifier,
            "final_price": final_price
        }
        
        return final_price, applied_rules, price_breakdown
    
    def _calculate_match_score(self, rule_conditions: Dict[str, Any], specifications: Dict[str, Any]) -> int:
        """Calculate how well the specifications match the rule conditions"""
        if not rule_conditions:
            return 0
        
        matches = 0
        total_conditions = len(rule_conditions)
        
        for key, expected_value in rule_conditions.items():
            if key in specifications:
                spec_value = specifications[key]
                
                # Exact match
                if spec_value == expected_value:
                    matches += 1
                # For numeric values, check if within range (if expected_value is a range)
                elif isinstance(expected_value, dict) and "min" in expected_value and "max" in expected_value:
                    try:
                        numeric_value = float(spec_value)
                        if expected_value["min"] <= numeric_value <= expected_value["max"]:
                            matches += 1
                    except (ValueError, TypeError):
                        continue
        
        # Return percentage match (0-100)
        return int((matches / total_conditions) * 100) if total_conditions > 0 else 0
    
    def _apply_price_rule(self, rule: PriceRule, base_price: int = None) -> int:
        """Apply the pricing rule to calculate final price"""
        starting_price = base_price or rule.base_price
        
        if rule.modifier_type == "add":
            return starting_price + rule.price_modifier
        elif rule.modifier_type == "multiply":
            multiplier = rule.price_modifier / 100  # Assuming modifier is in percentage
            return int(starting_price * (1 + multiplier))
        elif rule.modifier_type == "set":
            return rule.price_modifier
        else:
            logger.warning(f"Unknown modifier type: {rule.modifier_type}")
            return starting_price
    
    def create_price_rule(
        self, 
        subcategory_id: int,
        spec_conditions: Dict[str, Any],
        base_price: int,
        price_modifier: int = 0,
        modifier_type: str = "add",
        specification_template_id: int = None
    ) -> PriceRule:
        """Create a new price rule"""
        
        price_rule = PriceRule(
            subcategory_id=subcategory_id,
            specification_template_id=specification_template_id,
            spec_conditions=spec_conditions,
            base_price=base_price,
            price_modifier=price_modifier,
            modifier_type=modifier_type
        )
        
        self.db.add(price_rule)
        self.db.commit()
        self.db.refresh(price_rule)
        
        return price_rule
    
    def get_pricing_suggestions(self, subcategory_id: int) -> List[Dict[str, Any]]:
        """Get pricing suggestions based on existing rules and spec templates"""
        
        # Get spec templates for this subcategory
        spec_templates = self.db.query(SpecificationTemplate).filter(
            SpecificationTemplate.subcategory_id == subcategory_id,
            SpecificationTemplate.is_active == True,
            SpecificationTemplate.affects_price == True
        ).all()
        
        suggestions = []
        
        for template in spec_templates:
            if template.spec_type == "select" and template.spec_options:
                for option in template.spec_options:
                    # Check if we already have a rule for this option
                    existing_rule = self.db.query(PriceRule).filter(
                        PriceRule.subcategory_id == subcategory_id,
                        PriceRule.spec_conditions.contains({template.spec_name: option})
                    ).first()
                    
                    if not existing_rule:
                        suggestions.append({
                            "spec_name": template.spec_name,
                            "spec_value": option,
                            "suggested_condition": {template.spec_name: option},
                            "needs_pricing": True
                        })
        
        return suggestions
    
    def validate_specifications(self, subcategory_id: int, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specifications against the subcategory's spec templates"""
        
        spec_templates = self.db.query(SpecificationTemplate).filter(
            SpecificationTemplate.subcategory_id == subcategory_id,
            SpecificationTemplate.is_active == True
        ).all()
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Create lookup for templates
        templates_by_name = {template.spec_name: template for template in spec_templates}
        
        # Check required fields
        for template in spec_templates:
            if template.is_required and template.spec_name not in specifications:
                validation_result["errors"].append(
                    f"Required specification '{template.spec_name}' is missing"
                )
                validation_result["is_valid"] = False
        
        # Validate provided specifications
        for spec_name, spec_value in specifications.items():
            if spec_name not in templates_by_name:
                validation_result["warnings"].append(
                    f"Unknown specification '{spec_name}' provided"
                )
                continue
            
            template = templates_by_name[spec_name]
            
            # Type validation
            if template.spec_type == "select":
                if template.spec_options and spec_value not in template.spec_options:
                    validation_result["errors"].append(
                        f"Invalid value '{spec_value}' for '{spec_name}'. "
                        f"Valid options: {', '.join(template.spec_options)}"
                    )
                    validation_result["is_valid"] = False
            
            elif template.spec_type == "number":
                try:
                    float(spec_value)
                except (ValueError, TypeError):
                    validation_result["errors"].append(
                        f"'{spec_name}' must be a number, got '{spec_value}'"
                    )
                    validation_result["is_valid"] = False
            
            elif template.spec_type == "boolean":
                if not isinstance(spec_value, bool):
                    validation_result["errors"].append(
                        f"'{spec_name}' must be a boolean, got '{spec_value}'"
                    )
                    validation_result["is_valid"] = False
        
        return validation_result