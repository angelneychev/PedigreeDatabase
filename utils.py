"""
Utility functions for PedigreeDatabase
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from models import Dog
import math

def calculate_inbreeding_coefficient(dog: Dog, db: Session, generations: int = 5) -> Dict[str, Any]:
    """
    Calculate inbreeding coefficient using Wright's coefficient of inbreeding.
    
    Wright's Formula: F = Σ(1/2)^(n1+n2+1) * (1+FA)
    Where:
    - F = inbreeding coefficient
    - n1 = generations from individual to common ancestor through sire
    - n2 = generations from individual to common ancestor through dam  
    - FA = inbreeding coefficient of the common ancestor (simplified to 0)
    
    Returns: Dictionary with COI percentage, detailed breakdown, and common ancestors
    """    # Check if both parents exist (get actual integer IDs)
    sire_id = getattr(dog, 'sire_id', None)
    dam_id = getattr(dog, 'dam_id', None)
    
    if not sire_id or not dam_id:
        return {
            "coi_percentage": 0.0,
            "common_ancestors": [],
            "paths_analyzed": 0,
            "generations_analyzed": generations,
            "error": "Incomplete pedigree - both parents required for COI calculation"
        }
    
    # Get all ancestors from sire line
    sire_ancestors = _get_ancestors_with_paths(sire_id, db, generations, "sire")
    # Get all ancestors from dam line  
    dam_ancestors = _get_ancestors_with_paths(dam_id, db, generations, "dam")
    
    # Find common ancestors between sire and dam lines
    common_ancestor_ids = set(sire_ancestors.keys()) & set(dam_ancestors.keys())
    
    if not common_ancestor_ids:
        return {
            "coi_percentage": 0.0,
            "common_ancestors": [],
            "paths_analyzed": len(sire_ancestors) + len(dam_ancestors),
            "generations_analyzed": generations,
            "message": "No common ancestors found within specified generations"
        }
    
    # Calculate COI contribution from each common ancestor
    total_coi = 0.0
    common_ancestors_details = []
    
    for ancestor_id in common_ancestor_ids:
        # Get ancestor details
        ancestor_dog = db.query(Dog).filter(Dog.id == ancestor_id).first()
        if not ancestor_dog:
            continue
        
        # Get paths to this ancestor from both sides
        sire_paths = sire_ancestors[ancestor_id]
        dam_paths = dam_ancestors[ancestor_id]
        
        ancestor_coi_contribution = 0.0
        
        # Calculate contribution for each path combination
        for sire_path_length in sire_paths:
            for dam_path_length in dam_paths:
                # Wright's formula: (1/2)^(n1+n2+1) * (1+FA)
                # We assume FA = 0 for simplicity (ancestor not inbred)
                contribution = (0.5 ** (sire_path_length + dam_path_length + 1)) * 1.0
                ancestor_coi_contribution += contribution
        
        total_coi += ancestor_coi_contribution
        
        common_ancestors_details.append({
            "ancestor": {
                "id": ancestor_dog.id,
                "name": ancestor_dog.name,
                "registration_number": ancestor_dog.registration_number
            },
            "coi_contribution": ancestor_coi_contribution,
            "coi_contribution_percentage": round(ancestor_coi_contribution * 100, 4),
            "path_combinations": len(sire_paths) * len(dam_paths),
            "sire_paths": len(sire_paths),
            "dam_paths": len(dam_paths)
        })
    
    # Sort by contribution (highest first)
    common_ancestors_details.sort(key=lambda x: x["coi_contribution"], reverse=True)
    
    return {
        "coi_percentage": round(total_coi * 100, 4),
        "coi_decimal": round(total_coi, 6),
        "common_ancestors": common_ancestors_details,
        "common_ancestor_count": len(common_ancestors_details),
        "paths_analyzed": len(sire_ancestors) + len(dam_ancestors),
        "generations_analyzed": generations,
        "interpretation": _interpret_coi(total_coi * 100)
    }


def _get_ancestors_with_paths(dog_id: int, db: Session, max_generations: int, line: str) -> Dict[int, List[int]]:
    """
    Get all ancestors of a dog with their path lengths.
    Returns dict: {ancestor_id: [list_of_path_lengths_to_reach_ancestor]}
    """
    ancestors = {}
    
    def explore_ancestors(current_dog_id: int, current_generation: int):
        if current_generation > max_generations:
            return
        
        # Get current dog
        current_dog = db.query(Dog).filter(Dog.id == current_dog_id).first()
        if not current_dog:
            return
          # Add this dog to ancestors (including generation 0 for parent-level inbreeding)
        if current_dog_id not in ancestors:
            ancestors[current_dog_id] = []
        ancestors[current_dog_id].append(current_generation)
          # Continue to parents if within generation limit
        if current_generation < max_generations:
            sire_id = getattr(current_dog, 'sire_id', None)
            dam_id = getattr(current_dog, 'dam_id', None)
            
            if sire_id:
                explore_ancestors(sire_id, current_generation + 1)
            if dam_id:
                explore_ancestors(dam_id, current_generation + 1)
    
    # Start exploration from the given dog
    explore_ancestors(dog_id, 0)
    return ancestors

def _interpret_coi(coi_percentage: float) -> Dict[str, str]:
    """Interpret COI percentage and provide guidance"""
    if coi_percentage == 0.0:
        return {
            "level": "none",
            "description": "No inbreeding detected",
            "guidance": "No common ancestors found within analyzed generations.",
            "color": "#28a745"  # Green
        }
    elif coi_percentage < 3.125:
        return {
            "level": "very_low",
            "description": "Very low inbreeding",
            "guidance": "Minimal inbreeding. Generally acceptable for breeding.",
            "color": "#28a745"  # Green
        }
    elif coi_percentage < 6.25:
        return {
            "level": "low",
            "description": "Low inbreeding",
            "guidance": "Low level of inbreeding. Consider pedigree diversity in breeding decisions.",
            "color": "#ffc107"  # Yellow
        }
    elif coi_percentage < 12.5:
        return {
            "level": "moderate",
            "description": "Moderate inbreeding",
            "guidance": "Moderate inbreeding (equivalent to cousins breeding). Monitor for genetic issues.",
            "color": "#fd7e14"  # Orange
        }
    elif coi_percentage < 25.0:
        return {
            "level": "high",
            "description": "High inbreeding",
            "guidance": "High inbreeding (equivalent to half-siblings breeding). Careful health monitoring recommended.",
            "color": "#dc3545"  # Red
        }
    else:
        return {
            "level": "very_high",
            "description": "Very high inbreeding",
            "guidance": "Very high inbreeding (equivalent to full siblings/parent-offspring). Significant genetic risks.",
            "color": "#6f42c1"  # Purple
        }

def detect_pedigree_inbreeding(dog: Dog, generations: int = 4) -> Dict[str, List[Dict]]:
    """
    Detect inbreeding by finding common ancestors in pedigree up to specified generations.
    Uses the same logic as calculate_inbreeding_coefficient to ensure consistency.
    Returns dictionary with inbred dogs and their highlight colors.
    """
    # Use the same helper function as COI calculation
    sire_id = getattr(dog, 'sire_id', None)
    dam_id = getattr(dog, 'dam_id', None)
    
    if not sire_id or not dam_id:
        return {}
    
    # Import here to avoid circular imports
    from database import get_db
    db = next(get_db())
    
    # Get ancestors from both sides using same logic as COI
    sire_ancestors = _get_ancestors_with_paths(sire_id, db, generations, "sire")
    dam_ancestors = _get_ancestors_with_paths(dam_id, db, generations, "dam")
    
    # Find common ancestors
    common_ancestor_ids = set(sire_ancestors.keys()) & set(dam_ancestors.keys())
    
    if not common_ancestor_ids:
        return {}
    
    # Create result dictionary with highlighting information
    inbred_ancestors = {}
    highlight_colors = [
        '#FFE6E6',  # Light red
        '#E6F3FF',  # Light blue  
        '#E6FFE6',  # Light green
        '#FFF0E6',  # Light orange
        '#F0E6FF',  # Light purple
        '#FFFFE6',  # Light yellow
    ]
    
    color_index = 0
    for ancestor_id in common_ancestor_ids:
        # Get ancestor details
        ancestor_dog = db.query(Dog).filter(Dog.id == ancestor_id).first()
        if not ancestor_dog:
            continue
            
        highlight_color = highlight_colors[color_index % len(highlight_colors)]
        
        # Count total occurrences (sum of paths from both sides)
        sire_paths_count = len(sire_ancestors[ancestor_id])
        dam_paths_count = len(dam_ancestors[ancestor_id])
        total_occurrences = sire_paths_count + dam_paths_count
        
        inbred_ancestors[str(ancestor_id)] = {  # Convert to string key for template
            'dog': ancestor_dog,  # Dog object
            'color': highlight_color,
            'color_index': color_index + 1,  # 1-based index for CSS class
            'count': total_occurrences,
            'sire_paths': sire_paths_count,
            'dam_paths': dam_paths_count
        }
        color_index += 1
    
    return inbred_ancestors

def get_pedigree_completeness(dog: Dog, db: Session, generations: int = 3) -> Dict[str, float]:
    """
    Calculate pedigree completeness percentage for specified generations
    """
    def count_ancestors(current_dog: Dog, current_gen: int, max_gen: int) -> tuple:
        if current_gen > max_gen or not current_dog:
            return 0, 0
        
        # Count this dog as known
        known = 1
        total = 1
        
        if current_gen < max_gen:
            # Count ancestors
            sire_known, sire_total = count_ancestors(current_dog.sire, current_gen + 1, max_gen)
            dam_known, dam_total = count_ancestors(current_dog.dam, current_gen + 1, max_gen)
            
            known += sire_known + dam_known
            total += sire_total + dam_total
        
        return known, total
    
    known_ancestors, total_possible = count_ancestors(dog, 0, generations)
    
    if total_possible == 0:
        return {"percentage": 0.0, "known": 0, "total": 0}
    
    percentage = (known_ancestors / total_possible) * 100
    
    return {
        "percentage": round(percentage, 2),
        "known": known_ancestors,
        "total": total_possible
    }

def get_health_summary(dog: Dog) -> Dict[str, str]:
    """
    Get a summary of health test results for a dog
    """
    if not dog.health_tests:
        return {"status": "unknown", "message": "No health tests recorded"}
    
    # Analyze health test results
    good_results = ["+/+", "A", "0", "clear"]
    warning_results = ["B", "1", "carrier"]
    bad_results = ["-/-", "D", "E", "2", "3", "affected"]
    
    has_good = any(test.result in good_results for test in dog.health_tests)
    has_warning = any(test.result in warning_results for test in dog.health_tests)
    has_bad = any(test.result in bad_results for test in dog.health_tests)
    
    if has_bad:
        return {"status": "concern", "message": "Some health concerns detected"}
    elif has_warning:
        return {"status": "warning", "message": "Carrier status or minor concerns"}
    elif has_good:
        return {"status": "good", "message": "Good health test results"}
    else:
        return {"status": "unknown", "message": "Health test results unclear"}

def search_related_dogs(dog: Dog, db: Session, relationship_type: str = "all") -> List[Dog]:
    """
    Find related dogs (siblings, half-siblings, offspring)
    """
    related_dogs = []
    
    if relationship_type in ["all", "siblings", "half-siblings"]:
        # Find full siblings (same sire and dam)
        if dog.sire_id and dog.dam_id:
            full_siblings = db.query(Dog).filter(
                Dog.sire_id == dog.sire_id,
                Dog.dam_id == dog.dam_id,
                Dog.id != dog.id
            ).all()
            related_dogs.extend(full_siblings)
        
        # Find half-siblings (same sire OR same dam, but not both)
        if relationship_type in ["all", "half-siblings"]:
            if dog.sire_id:
                paternal_siblings = db.query(Dog).filter(
                    Dog.sire_id == dog.sire_id,
                    Dog.dam_id != dog.dam_id,
                    Dog.id != dog.id
                ).all()
                related_dogs.extend(paternal_siblings)
            
            if dog.dam_id:
                maternal_siblings = db.query(Dog).filter(
                    Dog.dam_id == dog.dam_id,
                    Dog.sire_id != dog.sire_id,
                    Dog.id != dog.id
                ).all()
                related_dogs.extend(maternal_siblings)
    
    if relationship_type in ["all", "offspring"]:
        # Find offspring where this dog is the sire
        if dog.sex == "Male":
            offspring_as_sire = db.query(Dog).filter(Dog.sire_id == dog.id).all()
            related_dogs.extend(offspring_as_sire)
        
        # Find offspring where this dog is the dam
        if dog.sex == "Female":
            offspring_as_dam = db.query(Dog).filter(Dog.dam_id == dog.id).all()
            related_dogs.extend(offspring_as_dam)
    
    # Remove duplicates
    unique_dogs = []
    seen_ids = set()
    for related_dog in related_dogs:
        if related_dog.id not in seen_ids:
            unique_dogs.append(related_dog)
            seen_ids.add(related_dog.id)
    
    return unique_dogs

def calculate_age_from_birth_date(birth_date) -> Optional[str]:
    """
    Calculate age in years and months from birth date
    """
    if not birth_date:
        return None
    
    from datetime import date
    today = date.today()
    
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    
    if months < 0:
        years -= 1
        months += 12
    elif months == 0 and today.day < birth_date.day:
        years -= 1
        months = 11
    
    if years == 0:
        return f"{months} month{'s' if months != 1 else ''}"
    elif months == 0:
        return f"{years} year{'s' if years != 1 else ''}"
    else:
        return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"

def validate_pedigree_rules(dog_data: dict, db: Session) -> List[str]:
    """
    Validate pedigree rules and return list of warnings/errors
    """
    warnings = []
    
    # Check if sire is male and dam is female
    if dog_data.get("sire_id"):
        sire = db.query(Dog).filter(Dog.id == dog_data["sire_id"]).first()
        if sire and sire.sex != "Male":
            warnings.append(f"Sire '{sire.name}' is not marked as Male")
    
    if dog_data.get("dam_id"):
        dam = db.query(Dog).filter(Dog.id == dog_data["dam_id"]).first()
        if dam and dam.sex != "Female":
            warnings.append(f"Dam '{dam.name}' is not marked as Female")
    
    # Check birth date logic
    if dog_data.get("date_of_birth"):
        birth_date = dog_data["date_of_birth"]
        
        if dog_data.get("sire_id"):
            sire = db.query(Dog).filter(Dog.id == dog_data["sire_id"]).first()
            if sire and sire.date_of_birth and sire.date_of_birth >= birth_date:
                warnings.append(f"Sire '{sire.name}' birth date should be before offspring birth date")
        
        if dog_data.get("dam_id"):
            dam = db.query(Dog).filter(Dog.id == dog_data["dam_id"]).first()
            if dam and dam.date_of_birth and dam.date_of_birth >= birth_date:
                warnings.append(f"Dam '{dam.name}' birth date should be before offspring birth date")
    
    return warnings

def get_breeding_statistics(db: Session) -> Dict:
    """
    Get general breeding statistics for the database
    """
    total_dogs = db.query(Dog).count()
    males = db.query(Dog).filter(Dog.sex == "Male").count()
    females = db.query(Dog).filter(Dog.sex == "Female").count()
    
    # Dogs with complete pedigree (both parents known)
    complete_pedigree = db.query(Dog).filter(
        Dog.sire_id.isnot(None),
        Dog.dam_id.isnot(None)
    ).count()
    
    # Dogs used for breeding
    used_as_sire = db.query(Dog).filter(Dog.id.in_(
        db.query(Dog.sire_id).filter(Dog.sire_id.isnot(None)).distinct()
    )).count()
    
    used_as_dam = db.query(Dog).filter(Dog.id.in_(
        db.query(Dog.dam_id).filter(Dog.dam_id.isnot(None)).distinct()
    )).count()
    
    return {
        "total_dogs": total_dogs,
        "males": males,
        "females": females,
        "complete_pedigree": complete_pedigree,
        "complete_pedigree_percentage": round((complete_pedigree / total_dogs * 100) if total_dogs > 0 else 0, 1),
        "used_as_sire": used_as_sire,
        "used_as_dam": used_as_dam,
        "total_breeding_dogs": used_as_sire + used_as_dam
    }
