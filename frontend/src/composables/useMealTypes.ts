/**
 * Shared meal type configuration.
 * Used by CampPlanner and DayDetail to avoid duplication.
 */
import { useI18n } from './useI18n'

const { t } = useI18n()

export const MEAL_TYPES = [
  { val: 'BREAKFAST', label: t('meal_type.breakfast') },
  { val: 'MORNING_SNACK', label: t('meal_type.morning_snack') },
  { val: 'LUNCH', label: t('meal_type.lunch') },
  { val: 'AFTERNOON_SNACK', label: t('meal_type.afternoon_snack') },
  { val: 'DINNER', label: t('meal_type.dinner') },
  { val: 'DESSERT', label: t('meal_type.dessert') },
]

export type MealTypeValue = (typeof MEAL_TYPES)[number]['val']

export function getMealTypeLabel(val: string): string {
  return MEAL_TYPES.find((mt) => mt.val === val)?.label || val
}
