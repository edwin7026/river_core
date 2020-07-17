# See LICENSE for details

require_relative '../riscv_base'

class RandomTemplate < RiscVBaseTemplate

  def run
    int_dist = dist(range(:value => 0,                                      :bias => 5), # Zero
                    range(:value => -1,                                     :bias => 5), # Small
                    range(:value => 0x0000000000000000..0x00000000ffffFFFF, :bias => 90)) # Large

    sequence {
      remw(x(_ FREE), x(_ FREE), x(_ FREE)) do situation('random_biased',
        :dist => dist(range(:value=> int_dist,                :bias => 80),  # Simple
                      range(:value=> [0xDEADBEEF, 0xBADF00D], :bias => 20))) # Magic
      end
      # NOP instruction is used as a location to return from en exception
      nop
    }.run 10000
  end

end