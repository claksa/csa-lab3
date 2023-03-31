db 3
mov br 2
mov acc 2
mod acc br
ld r7 0
sv r7 1
add acc 1
test acc
jz math
jmp end
math:
    mov acc 4
    mod acc 2
    mov acc 4
    mul 2
end:
    halt
