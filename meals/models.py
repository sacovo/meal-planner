from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Camp(models.fields.UUIDField):
    pass # Wait, let's use standard inheritance

class Camp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    default_people_count = models.PositiveIntegerField(default=10)
    start_date = models.DateField()
    end_date = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="camps")
    collaborators = models.ManyToManyField(User, related_name="collaboration_camps", blank=True)
    notes = models.TextField(blank=True, help_text="General notes for the camp (e.g., special events, allergies summary)")

    def __str__(self):
        return self.name


class IngredientCategory(models.TextChoices):
    PRODUCE = "PRODUCE", "Produce / Vegetables / Fruit"
    MEAT = "MEAT", "Meat / Poultry / Seafood"
    DAIRY = "DAIRY", "Dairy / Fridge"
    PANTRY = "PANTRY", "Pantry / Dry Goods"
    SPICES = "SPICES", "Spices / Condiments"
    BREAD = "BREAD", "Bakery / Bread"
    DRINKS = "DRINKS", "Drinks"
    FROZEN = "FROZEN", "Frozen"
    NON_FOOD = "NON_FOOD", "Non-Food / General"
    OTHER = "OTHER", "Other"


class Ingredient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    category = models.CharField(
        max_length=50,
        choices=IngredientCategory.choices,
        default=IngredientCategory.OTHER,
    )
    base_unit = models.CharField(max_length=50, help_text="e.g. grams, pieces, ml")

    def __str__(self):
        return self.name

class DietaryPreference(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name


class IngredientUnitConversion(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="conversions")
    unit_name = models.CharField(max_length=50, help_text="e.g. tbsp, tsp, piece, kilogram")
    multiplier = models.FloatField(help_text="Multiply by this to get base_unit")
    needs_review = models.BooleanField(default=False, help_text="Set to true if automatically captured from a recipe and needs admin conversion factor")

    class Meta:
        unique_together = ("ingredient", "unit_name")

    def __str__(self):
        return f"{self.unit_name} -> {self.multiplier} {self.ingredient.base_unit}"


class Recipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes", null=True, blank=True)
    tags = models.JSONField(default=list, blank=True, help_text="List of dietary tags like Vegan, Gluten-Free")
    preferences = models.ManyToManyField(DietaryPreference, related_name="recipes", blank=True)
    default_portions = models.PositiveIntegerField(default=1, help_text="How many people this recipe serves as written")
    is_importing = models.BooleanField(default=False, help_text="True if AI is currently parsing this recipe in the background")

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.RESTRICT)
    amount = models.FloatField()
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.amount} {self.unit} {self.ingredient.name}"


class MealType(models.TextChoices):
    BREAKFAST = "BREAKFAST", "Breakfast"
    MORNING_SNACK = "MORNING_SNACK", "Morning Snack (Z'nüni)"
    LUNCH = "LUNCH", "Lunch"
    AFTERNOON_SNACK = "AFTERNOON_SNACK", "Afternoon Snack (Z'vieri)"
    DINNER = "DINNER", "Dinner"
    DESSERT = "DESSERT", "Dessert"
    NIGHT_SNACK = "NIGHT_SNACK", "Night Snack"


class CampMeal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name="meals")
    recipe = models.ForeignKey(Recipe, on_delete=models.RESTRICT)
    meal_type = models.CharField(max_length=50, choices=MealType.choices)
    date = models.DateField()
    override_people_count = models.PositiveIntegerField(null=True, blank=True, help_text="Overrides camp's default count")
    serves_preference = models.ForeignKey(DietaryPreference, on_delete=models.SET_NULL, null=True, blank=True, help_text="If this meal slot serves a specific subgroup")
    leftovers_noted = models.TextField(blank=True, help_text="Note what was left over after meal")
    is_done = models.BooleanField(default=False, help_text="Mark if this meal has been cooked/consumed")

    class Meta:
        ordering = ["date", "meal_type"]

    @property
    def people_count(self):
        return self.override_people_count if self.override_people_count is not None else self.camp.default_people_count

    def __str__(self):
        return f"{self.camp.name} - {self.date} {self.get_meal_type_display()}"


class GeneralCampItem(models.Model):
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name="general_items")
    name = models.CharField(max_length=255)
    amount = models.CharField(max_length=50)
    category = models.CharField(
        max_length=50,
        choices=IngredientCategory.choices,
        default=IngredientCategory.NON_FOOD,
    )

    def __str__(self):
        return f"{self.amount} {self.name}"


class ShoppingList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name="shopping_lists")
    meals = models.ManyToManyField(CampMeal, related_name="shopping_lists", blank=True)
    shared_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shopping List for {self.camp.name}"


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="items")
    # For ingredients aggregated from recipes
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, null=True, blank=True)
    # For custom general items
    custom_name = models.CharField(max_length=255, blank=True)
    
    amount = models.FloatField()
    unit = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    is_checked = models.BooleanField(default=False)
    source_meals_text = models.JSONField(default=list, blank=True, help_text="List of descriptions marking where this came from")

    class Meta:
        ordering = ["category", "ingredient__name", "custom_name"]


class Inventory(models.Model):
    camp = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name="inventory")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_bought = models.FloatField(default=0)
    quantity_used = models.FloatField(default=0)
    unit = models.CharField(max_length=50)

    class Meta:
        unique_together = ("camp", "ingredient")
