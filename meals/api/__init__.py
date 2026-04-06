"""Meals API package — assembles sub-routers into a single router."""

from ninja import Router

from . import camps, ingredients, inventory, meals, recipes, shopping

router = Router()

router.add_router("", camps.router)
router.add_router("", recipes.router)
router.add_router("", ingredients.router)
router.add_router("", meals.router)
router.add_router("", shopping.router)
router.add_router("", inventory.router)
