class Bank:

    def checker(self, serial_number, key, flag="CREDIT_ORG", bic="044525225", val="810", type_of_number="40817"):
        mask = "71371371371371371371371"

        if flag == "RKC":
            condition_number = "0" + bic[4:6]
        elif flag == "CREDIT_ORG":
            condition_number = bic[6:]

        user_number = type_of_number + val + str(key) + "0000" + serial_number

        number = condition_number + user_number

        sum = 0

        for i in range(len(mask)):

            product = int(number[i]) * int(mask[i])

            sum += product % 10
        
        sum = sum % 10 * 3

        control_key = sum % 10

        if control_key == 0:
            return 1

        elif self.checker(serial_number, control_key, flag, bic, val, type_of_number) == 1:
                return control_key
        else:
             raise("Ошибка подбора ключа!")
        
        

repository = Bank()
print(repository.checker("0000025", "0", bic="049805746", val="810", type_of_number="40602"))

