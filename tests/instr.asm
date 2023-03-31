db 3
mov br 5
ld r7 0
sv r7 1
add acc 1
test acc
jz math
jmp end
math:
    mov acc 4
    mod 2
    mov acc 4
    div 2
    mul 2
end:
    halt
