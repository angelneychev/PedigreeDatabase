"""
Utility functions for PedigreeDatabase
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from models import Dog
import math

def calculate_inbreeding_coefficient(dog: Dog, db: Session, generations: int = 5) -> float:
    """
    Calculate inbreeding coefficient using Wright's coefficient of inbreeding.
    This is a placeholder implementation - the actual algorithm is complex.
    """
    # TODO: Implement actual inbreeding coefficient calculation
    # This requires building a pedigree tree and finding common ancestors
    return 0.0

def detect_pedigree_inbreeding(dog: Dog, generations: int = 4) -> Dict[str, List[Dict]]:
    """
    Detect inbreeding by finding common ancestors in pedigree up to specified generations.
    Returns dictionary with inbred dogs and their highlight colors.
    """
    def get_all_ancestors(current_dog: Dog, current_gen: int, max_gen: int, path: str = "") -> List[Dict]:
        """Recursively collect all ancestors with their positions in pedigree"""
        if current_gen >= max_gen or not current_dog:
            return []
        
        ancestors = []
        if current_dog:
            ancestors.append({
                'dog': current_dog,
                'generation': current_gen,
                'path': path,
                'id': current_dog.id,
                'name': current_dog.name
            })
            
            if current_gen < max_gen - 1:
                # Get sire's ancestors
                if current_dog.sire:
                    sire_ancestors = get_all_ancestors(
                        current_dog.sire, 
                        current_gen + 1, 
                        max_gen, 
                        f"{path}_sire"
                    )
                    ancestors.extend(sire_ancestors)
                
                # Get dam's ancestors
                if current_dog.dam:
                    dam_ancestors = get_all_ancestors(
                        current_dog.dam, 
                        current_gen + 1, 
                        max_gen, 
                        f"{path}_dam"
                    )
                    ancestors.extend(dam_ancestors)
        
        return ancestors
    
    # Get all ancestors starting from the dog's parents
    all_ancestors = []
    if dog.sire:
        sire_ancestors = get_all_ancestors(dog.sire, 1, generations, "sire")
        all_ancestors.extend(sire_ancestors)
    
    if dog.dam:
        dam_ancestors = get_all_ancestors(dog.dam, 1, generations, "dam")
        all_ancestors.extend(dam_ancestors)
    
    # Find common ancestors (inbreeding)
    ancestor_occurrences = {}
    for ancestor in all_ancestors:
        ancestor_id = ancestor['id']
        if ancestor_id not in ancestor_occurrences:
            ancestor_occurrences[ancestor_id] = []
        ancestor_occurrences[ancestor_id].append(ancestor)
    
    # Identify inbred ancestors (appearing more than once)
    inbred_ancestors = {}
    highlight_colors = [
        '#FFE6E6',  # Light red
        '#E6F3FF',  # Light blue  
        '#E6FFE6',  # Light green
        '#FFF0E6',  # Light orange        '#F0E6FF',  # Light purple
        '#FFFFE6',  # Light yellow
    ]
    
    color_index = 0
    for ancestor_id, occurrences in ancestor_occurrences.items():
        if len(occurrences) > 1:  # Appears more than once = inbreeding
            highlight_color = highlight_colors[color_index % len(highlight_colors)]
            inbred_ancestors[str(ancestor_id)] = {  # Convert to string key for template
                'dog': occurrences[0]['dog'],  # Dog object
                'occurrences': occurrences,
                'color': highlight_color,
                'color_index': color_index + 1,  # 1-based index for CSS class
                'count': len(occurrences)
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
