
def calculate_tax(income):
    """
    Рассчитывает налог на доходы (НДФЛ) по прогрессивной шкале.
    """
    if income <= 5_000_000:
        tax = income * 0.13
    else:
        tax = 5_000_000 * 0.13 + (income - 5_000_000) * 0.15
    return tax


def main():
    try:
        income = float(input("Введите ваш годовой доход (в рублях): "))
        if income < 0:
            print("Доход не может быть отрицательным.")
            return

        tax = calculate_tax(income)
        print(f"\nСумма налога к уплате за год: {tax:,.2f} руб.")

        # Дополнительная информация
        if income <= 5_000_000:
            print(f"Ставка: 13%")
        else:
            excess = income - 5_000_000
            print(f"Ставка: 13% на первые 5 млн руб. + 15% на сумму превышения ({excess:,.2f} руб.)")

        print(f"Чистый доход после уплаты налога: {income - tax:,.2f} руб.")

    except ValueError:
        print("Ошибка: введите число.")


if __name__ == "__main__":
    main()